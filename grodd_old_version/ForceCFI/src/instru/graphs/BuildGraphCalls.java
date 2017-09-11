package instru.graphs;

import instru.util.Stat;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.StringTokenizer;
import java.util.Vector;

import org.apache.commons.lang3.StringEscapeUtils;

import soot.Body;
import soot.BodyTransformer;
import soot.Unit;
import soot.toolkits.graph.pdg.EnhancedUnitGraph;

/**
 * BuildGraphCalls is a Soot transformation that build .dot files from the considered APK.
 * 
 * @deprecated use CfgBuilder instead
 */
@Deprecated
public class BuildGraphCalls extends BodyTransformer {

	boolean startingBlock;
	
	private int nbName = 0;
	private HashMap<Unit, String> unitNames = new HashMap<Unit, String>();

	private HashSet<String> seenTags;
	public int nbAnalyzedMethods = 0;
	public int nbAnalyzedMethodsWithSeenInstructions = 0;
	private int nbJFLNodes = 0;
	private int nbJFLNodesWithSeenInstructions = 0;
	public HashMap<String, Stat> stats;
	
	private String dotOutputDir;
	
	/**
	 * 
	 * @param seenTags
	 * @param dotOutputDir
	 */
	public BuildGraphCalls(HashSet<String> seenTags, String dotOutputDir) {
		this.seenTags = seenTags;
		this.stats = new HashMap<String, Stat>();
		this.dotOutputDir = dotOutputDir;
	}
	
	@Override
	protected void internalTransform(Body body, String phase, Map<String, String> options) {
		String classMethodName = body.getMethod().getSignature();
		File f = new File(dotOutputDir + "/" + getShortClassMethodName(classMethodName) + ".dot");
		
		try {
			FileWriter fw = new FileWriter(f); // append
			fw.write("digraph G {\n");
			nbAnalyzedMethods++;
			
			computeGraph(body, classMethodName, fw);
			deepSearchGraph(body, classMethodName, fw);

			fw.write("}\n");
			fw.close();
		} catch (IOException e) {
			e.printStackTrace();
		}

		if (this.nbJFLNodesWithSeenInstructions > 0)
			nbAnalyzedMethodsWithSeenInstructions++;
		
		incrStatsForMethod(classMethodName);
	}
	
	/**
	 * 
	 * @param u
	 * @return
	 */
	private String getAndGenerateNodeName(Unit u) {
		String name = unitNames.get(u);
		if (name != null) {
			return name;
		}
		else {
			String newname = "N" + nbName++;
			unitNames.put(u, newname);
			return newname;
		}
	}
	
	/**
	 * 
	 * @param classMethodName
	 * @return
	 */
	public Stat getStatsForMethod(String classMethodName) {
		Stat i = stats.get(classMethodName);
		if (i == null) {
			i = new Stat();
			stats.put(classMethodName, i);
		}
		return i;
	}
	
	/**
	 * 
	 * @param classMethodName
	 */
	public void incrStatsForMethod(String classMethodName) {
		Stat statsForClass = getStatsForMethod(classMethodName);
		statsForClass.nbJFLNodesWithSeenInstructions += this.nbJFLNodesWithSeenInstructions;
		statsForClass.nbJFLNodes += this.nbJFLNodes;
	}
	
	/**
	 * 
	 * @param body
	 * @param classMethodName
	 * @param fw
	 * @throws IOException
	 */
	protected void deepSearchGraph(Body body, String classMethodName, FileWriter fw)
			throws IOException {
		EnhancedUnitGraph graph = null;
		try {
			graph = new EnhancedUnitGraph(body);
		}
		catch (NullPointerException e) {
			// To handle a bug in soot:
			// soot.toolkits.graph.pdg.EnhancedUnitGraph.handleExplicitThrowEdges
			// (EnhancedUnitGraph.java:205)
			return;
		}
		
		List<Unit> heads = graph.getHeads();
		if (heads.size() != 1) {
			System.err.println("Error: multiple entry points !");
			return;
		}

		Unit root = heads.get(0);
		HashMap<Unit, Boolean> marks = new HashMap<Unit, Boolean>();
		Vector<Unit> dependenciesTags = new Vector<Unit>();
		deepSearchGraphRecursive(body, root, graph, marks, dependenciesTags);

		for (Unit u : dependenciesTags)
			fw.write("\"" + protect(u) +  "\" [style=filled, color=darkorchid1]\n");
	}

	/**
	 * 
	 * @param body
	 * @param root
	 * @param graph
	 * @param marks
	 * @param dependenciesTags
	 */
	protected void deepSearchGraphRecursive(Body body, Unit root, EnhancedUnitGraph graph,
			HashMap<Unit, Boolean> marks, Vector<Unit> dependenciesTags) {
		// If node marked, then nothing to do (node already visited)
		if (marks.get(root) != null)
			return;
		
		// Mark the node
		marks.put(root, new Boolean(true));
		
		List<Unit> outEdges = graph.getSuccsOf(root);
		
		if (outEdges.size() == 0)    // No next (probably a "return")
			return;
		
		if (outEdges.size() == 1) {  // Simple statement
			Unit next = outEdges.get(0);
			deepSearchGraphRecursive(body, next, graph, marks, dependenciesTags);
		}
		
		if (outEdges.size() == 2) {  // Conditional branches (If)
			Unit t1 = outEdges.get(0);
			Unit t2 = outEdges.get(1);
			String bytecodeInstructionT1 = isJFLLogInstruction(t1);
			String bytecodeInstructionT2 = isJFLLogInstruction(t2);
			if (bytecodeInstructionT1 != null && bytecodeInstructionT2 != null) {
				//System.out.println("considering " + bytecodeInstructionT1);
				if (seenTags.contains(bytecodeInstructionT1))
					deepSearchGraphRecursive(body, t1, graph, marks, dependenciesTags);
				else
					dependenciesTags.add(root);
				
				if (seenTags.contains(bytecodeInstructionT2))
					deepSearchGraphRecursive(body, t2, graph, marks, dependenciesTags);
				else
					dependenciesTags.add(root);
			}
		}
	}
	
	/**
	 * 
	 * @param classMethodName
	 * @return
	 */
	private String getShortClassMethodName(String classMethodName) {
		String res = new String(classMethodName);
		return res.replaceAll("(\\(.*\\))", "(" + (classMethodName.hashCode()) + ")" );
	}

	/**
	 * 
	 * @param body
	 * @param classMethodName
	 * @param fw
	 * @throws IOException
	 */
	protected void computeGraph(Body body, String classMethodName, FileWriter fw)
			throws IOException {
		nbJFLNodesWithSeenInstructions = 0;
		nbJFLNodes = 0;
		EnhancedUnitGraph graph = new EnhancedUnitGraph(body);
		List<Unit> heads = graph.getHeads();

		if (heads.size() != 1)
			System.err.println("Error: multiple entry points !");
	
		Iterator<Unit> i = body.getUnits().snapshotIterator();
		while (i.hasNext()) {
			Unit u = i.next();
			
			List<Unit> outEdges = graph.getSuccsOf(u);
			
			// Writing all edges
			for (Unit outE : outEdges)
				fw.write("\"" + protect(u) +  "\" -> \"" + protect(outE) + "\"\n");

			if (outEdges.size() == 2) {  // This is a branching
				Unit t1 = outEdges.get(0);
				Unit t2 = outEdges.get(1);
				String bytecodeInstructionT1 = isJFLLogInstruction(t1);
				String bytecodeInstructionT2 = isJFLLogInstruction(t2);
				if (bytecodeInstructionT1 != null && bytecodeInstructionT2 != null)
					if ( seenTags.contains(bytecodeInstructionT1)
					     && seenTags.contains(bytecodeInstructionT2) )
						fw.write("\"" + protect(u) +  "\" [style=filled, color=green]\n");
					else
						fw.write("\"" + protect(u) +  "\" [style=filled, color=red]\n");
			}
			
			// Writing special nodes color
			String bytecodeInstruction = isJFLLogInstruction(u);
			if (bytecodeInstruction != null) {  // It is a log instruction
				nbJFLNodes++;
				if ( seenTags.contains(bytecodeInstruction)) {  // I have seen it !
					fw.write("\"" + protect(u) +  "\" [style=filled, color=blue]\n");
					nbJFLNodesWithSeenInstructions++;
				}
			}
		}
	}
	
	/**
	 * 
	 * @param u
	 * @return
	 */
	private String protect(Unit u) {
		String bytecodeInstruction = isJFLLogInstruction(u);
		if (bytecodeInstruction == null)  // It is a regular instruction
			bytecodeInstruction = StringEscapeUtils.escapeEcmaScript(u.toString());
		
		return getAndGenerateNodeName(u) + " : " + bytecodeInstruction;
	}
	
	/**
	 * 
	 * @param u
	 * @return ??????
	 */
	private String isJFLLogInstruction(Unit u) {
		String res = StringEscapeUtils.escapeEcmaScript(u.toString());

		// Replacing ugly JFL invoke:
		if ( res.contains("JFL")
		     && !res.contains("goto") 
		     && (res.contains("BRANCH") || res.contains("BEGIN")) ) {
			// We have to find the tag from such a line:
			// staticinvoke <android.util.Log: int i(java.lang.String,java.lang.String)>(\"JFL\"...
			StringTokenizer st = new StringTokenizer(res, "\\\"");
			st.nextToken(); // Ugly but well...
			st.nextToken();
			st.nextToken();
			String tag = st.nextToken();

			return new String(tag);
		}
		else {
			return null;
		}
	}
	
	
	/**
	 * 
	 * @param captureLogcatFile
	 * @param totalCaptureLogcatFile
	 * @return
	 */
	public static HashSet<String> readSeenTags(String captureLogcatFile,
			String totalCaptureLogcatFile) {
		if (captureLogcatFile.isEmpty() || totalCaptureLogcatFile.isEmpty()) {
			System.out.println("No logcat TAGS provided.");
			return  new HashSet<String>();
		}
		
		HashSet<String> seenTags = new HashSet<String>();
		BufferedReader br;

		System.out.println("Reading last capture: " + captureLogcatFile);
		try {
			br = new BufferedReader(new FileReader(captureLogcatFile));
			String line = br.readLine();
			while (line != null) {
				seenTags.add(line);
				line = br.readLine();
			}
			br.close();
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
		System.out.println("Read " + seenTags.size() + " logcat TAGS.");
		
		HashSet<String> seenTagsOld = new HashSet<String>();
		System.out.println("Reading Old captures: " + totalCaptureLogcatFile);
		BufferedReader brT;
		try {
			brT = new BufferedReader(new FileReader(totalCaptureLogcatFile));
			String line = brT.readLine();
			while (line != null) {
				seenTagsOld.add(line);
				line = brT.readLine();
			}
			brT.close();			
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
		
		System.out.println("Read " + seenTagsOld.size() + " logcat TAGS.");
		seenTags.addAll(seenTagsOld);
		System.out.println("Total: " + seenTags.size() + " logcat TAGS.");
		System.out.println("Writing new captures: "+ totalCaptureLogcatFile);
		BufferedWriter bwT;
		try {
			bwT = new BufferedWriter(new FileWriter(totalCaptureLogcatFile));
			for (String tag : seenTags)
				bwT.write(tag + "\n");
			bwT.close();
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
		
		return seenTags;
	}
	
	/**
	 * 
	 * @param bgc
	 * @param dotOutputDir
	 */
	public void exportStats() {
		int nbMethods = 0;
		int nbMethodsTouched = 0;
		int nbJFLNodes = 0;
		int nbJFLNodesWithSeenInstructions = 0;
		System.out.println("Generating stats: " + dotOutputDir + "/stats.log");
		File f = new File(dotOutputDir + "/stats_all.log");
		File fp = new File(dotOutputDir + "/stats_partially.log");
		try {
			FileWriter stats = new FileWriter(f);
			FileWriter stats_partially = new FileWriter(fp);

			Set<String> classes = this.stats.keySet();
			for (String eachClassMethod : classes) {
				nbMethods++;
				Stat statsClass = getStatsForMethod(eachClassMethod);
				nbJFLNodes += statsClass.nbJFLNodes;
				nbJFLNodesWithSeenInstructions += statsClass.nbJFLNodesWithSeenInstructions;
					
				stats.write("" + eachClassMethod + " : " + statsClass + "\n");
				
				if (statsClass.nbJFLNodesWithSeenInstructions > 0)
					nbMethodsTouched++;
				
				if ( statsClass.nbJFLNodesWithSeenInstructions > 0
				     && statsClass.nbJFLNodesWithSeenInstructions < statsClass.nbJFLNodes )
					stats_partially.write("" + eachClassMethod + " : " + statsClass + "\n");
			}
			
			stats.close();
			stats_partially.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
		
		System.out.println("Number of methods: " + nbMethods);
		System.out.println("Number of methods partially executed: " + nbMethodsTouched);
		System.out.println("Number of JFL LOG points: " + nbJFLNodes);
		System.out.println("Number of JFL LOG points executed: " + nbJFLNodesWithSeenInstructions);
		System.out.println("END");
	}
}
