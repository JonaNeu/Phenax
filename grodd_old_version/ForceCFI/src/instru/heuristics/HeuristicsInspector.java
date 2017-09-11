package instru.heuristics;

import instru.Main;
import instru.heuristics.Alert.AlertType;
import instru.tags.BranchTagger;
import instru.tags.BranchTagger.TagType;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import soot.Body;
import soot.BodyTransformer;
import soot.G;
import soot.PatchingChain;
import soot.Type;
import soot.Unit;
import soot.Value;
import soot.ValueBox;

/**
 * This BodyTransformer applies heuristics loaded from a JSON config file to detect suspicious code
 * blocks, and logs them so they can be used in further analysis.
 */
public class HeuristicsInspector extends BodyTransformer {

	private List<String> packagesToIgnore = new ArrayList<>();
	private List<Heuristic> heuristics = new ArrayList<>();
	private Map<String, CodeTarget> targets = new HashMap<>();
	
	private String currentMethodSignature;
	private Body currentBody;
	
	/**
	 * Load a load of heuristics to use from a specifically formatted JSON file
	 * (see the appropriate doc for more info).
	 */
	public HeuristicsInspector(String heuristicsJsonFile) {
		JSONObject heuristicJson = null;
		try {
			JSONParser parser = new JSONParser();
			heuristicJson = (JSONObject) parser.parse(new FileReader(heuristicsJsonFile));
		} catch (IOException | ParseException e) {
			log("Failed to open or parse " + heuristicsJsonFile);
			e.printStackTrace();
		}
		
		JSONArray packagesArray = (JSONArray) heuristicJson.get("packages_to_ignore");
		for (Object obj : packagesArray)
			packagesToIgnore.add((String) obj);
		
		JSONArray categoriesArray = (JSONArray) heuristicJson.get("categories");
		for (Object obj : categoriesArray) {
			JSONObject dict = (JSONObject) obj;
			Heuristic heuristic = new Heuristic(dict);
			heuristics.add(heuristic);
		}
	}
	
	
	
	@Override
	protected void internalTransform(Body body, String phase, Map<String, String> options) {
		currentBody = body;
		currentMethodSignature = body.getMethod().getSignature();
		
		String bodyClass = body.getMethod().getDeclaringClass().getName();
		for (String packageToIgnore : packagesToIgnore) {
			if (bodyClass.startsWith(packageToIgnore)) {
				log("Ignoring " + currentMethodSignature);
				return;
			}
		}
		
		log("In " + currentMethodSignature);
		
		Iterator<Unit> i = body.getUnits().snapshotIterator();
		while (i.hasNext()) {
			Unit unit = i.next();
			inspectClasses(unit);
			checkGreppables(unit);
		}
	}
	
	/** Search for some specific types used by the instruction represented by this Unit. */
	private void inspectClasses(Unit unit) {
		List<Type> types = getTypesUsed(unit);
		
		for (Heuristic heuristic : heuristics) {
			for (String className : heuristic.classes) {
				for (Type type : types) {
					String typeName = type.toString();
					
					boolean match;
					if (className.endsWith(".*"))
						match = typeName.startsWith(className.substring(0, className.length() - 1));
					else
						match = typeName.equals(className);
					
					if (match) {
						log("\t" + heuristic.name + ": " + typeName);

						////// PUT NEW METHOD HERE
						
						CodeTarget target = getCurrentTarget();
						target.addAlert(AlertType.CLASS, heuristic, typeName, unit);
						
						List<String> branches = getBranchesToUnit(currentBody, unit);
						for (String branch : branches)
							log("Branch leading here: " + branch);
					}
				}
			}
		}
	}
	
	/** Check if any greppable pattern is found in the text representation of that instruction. */
	private void checkGreppables(Unit unit) {
		String searchable = unit.toString();
		
		for (Heuristic heuristic : heuristics) {
			for (String greppable : heuristic.greppable) {
				if (searchable.contains(greppable)) {
					log("\t" + heuristic.name + ": grepped " + greppable);
					
					CodeTarget target = getCurrentTarget();
					target.addAlert(AlertType.GREP, heuristic, greppable, unit);


				}
			}
		}
	}
	
	
	
	/** Wrapper to get the CodeTarget of the current method, whether it's already created or not. */
	private CodeTarget getCurrentTarget() {
		CodeTarget target = targets.get(currentMethodSignature);
		if (target == null) {
			target = new CodeTarget(currentMethodSignature);
			targets.put(currentMethodSignature, target);
		}
		return target;
	}
	
	/** Return a list of Type used by this Unit. */
	private List<Type> getTypesUsed(Unit unit) {
		List<Type> types = new ArrayList<>();
		for (ValueBox vb : unit.getUseBoxes()) {
			Value v = vb.getValue();
			types.add(v.getType());
		}
		return types;
	}
	
	private List<String> getBranchesToUnit(Body body, Unit unit) {
		List<String> branches = new ArrayList<>();
		PatchingChain<Unit> units = body.getUnits(); 
		
		while (unit != null) {
			unit = units.getPredOf(unit);
			String tag = Main.branchTagger.getUnitTagOrNull(unit);
			if (tag != null && BranchTagger.isTag(unit, TagType.BRANCH)) {
				branches.add(tag);
			}
		}
		
		return branches;
	}
	
	
	
	/** Log string s (at this moment, just in Soot's stdout). */
	private void log(String s) {
		G.v().out.println(s);
	}
	
	/** Write code targets data formatted in a JSON file to be reusable by other programs. */
	@SuppressWarnings("unchecked")
	public void writeTargetsList() {
		JSONArray targetsJsonList = new JSONArray();
		for (CodeTarget target : targets.values())
			targetsJsonList.add(target.toJson());
		String list = targetsJsonList.toString();
		
		File f = new File(Main.outputDir + "/targets.json");
		try {
			FileWriter fw = new FileWriter(f);
			fw.write(list);
			fw.close();
		} catch (IOException e) {
			System.err.println("Can't write in file " + f.getAbsolutePath());
		}
	}
	
	/** Output informations in a log file about what the inspector found. */
	public void writeInfos() {
		File f = new File(Main.outputDir + "/suspicious.log");
		try {
			FileWriter fw = new FileWriter(f);
			for (CodeTarget target : targets.values())
				fw.write(target.toString() + "\n");
			fw.close();
		} catch (IOException e) {
			System.err.println("Can't write in file " + f.getAbsolutePath());
		}
	}
	
}
