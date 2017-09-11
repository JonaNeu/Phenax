package instru;

import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.GnuParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import instru.force.BranchForcer;
import instru.graphs.CfgBuilder;
import instru.graphs.ImpGen;
import instru.heuristics.HeuristicsInspector;
import instru.tags.BranchTagger;
import instru.util.SignerAligner;
import soot.G;
import soot.Pack;
import soot.PackManager;
import soot.Transform;

/**
 * Parse given args, then perform several Soot transformations: tagging, graph
 * creation and branch forcing.
 */
public class Main {

	public static int nbrMethods = 0;

	public static String inputApk = "";
	public static String outputDir = "";
	public static String sootOutputDir = "";
	public static boolean addTags = false;
	// public static String captureLogcatFile = "";
	public static String impFile = "";
	public static String dotOutputDir = "";
	public static String superDir = "";
	public static String branchesFile = "";
	public static String heuristicsFile = "";

	public static BranchTagger branchTagger = new BranchTagger();
	public static BranchForcer branchForcer;
	public static CfgBuilder cfgBuilder;
	public static HeuristicsInspector heuristicsInspector;
	public static boolean doImplicit = false;
	public static boolean verbose = false;
	public static JSONObject heuristicJson = null;
	public static List<String> packagesToIgnore = new ArrayList<>();

	/** Parse options from command line data. */
	private static void setOptions(String[] args) {
		Options options = new Options();

		Option input = new Option("inputApk", true, "The apk file to parse.");
		input.setRequired(true);
		options.addOption(input);

		Option output = new Option("outputDir", true, "The output dir for the new apk to produce.");
		output.setRequired(true);
		options.addOption(output);

		Option addTagsOption = new Option("addTags", false, "Add method and branch tags");
		options.addOption(addTagsOption);

		Option impfileOption = new Option("impFile", true, "Implicit edges file");
		options.addOption(impfileOption);

		Option doImplicitOption = new Option("doImplicit", false, "Generate implicit edges");
		options.addOption(doImplicitOption);

		Option verboseOption = new Option("verbose", false, "Verbose mode");
		options.addOption(verboseOption);

		// Option captureLogcat = new Option(
		// "captureLogcat", true, "The capture of the logcat trace."
		// );
		// options.addOption(captureLogcat);

		Option dotOutput = new Option("dotOutputDir", true, "The output dir for the dot graphs (computes dot files).");
		options.addOption(dotOutput);

		Option branches = new Option("branches", true, "A file containing branch names to force");
		options.addOption(branches);

		Option heuristics = new Option("heuristics", true,
				"A JSON file containing heuristics for suspicious code targeting");
		options.addOption(heuristics);

		CommandLineParser parser = new GnuParser();
		CommandLine cmd = null;
		try {
			cmd = parser.parse(options, args);
		} catch (ParseException e) {
			G.v().out.println(e.getMessage());
			HelpFormatter hf = new HelpFormatter();
			hf.printHelp("ForceCFI: APK branch analyzer / forcer", options);
			System.exit(-1);
		}

		inputApk = cmd.getOptionValue("inputApk", "");
		outputDir = cmd.getOptionValue("outputDir", "");
		sootOutputDir = outputDir + "/apk";
		addTags = cmd.hasOption("addTags");
		impFile = cmd.getOptionValue("impFile", "");
		doImplicit = cmd.hasOption("doImplicit");
		verbose = cmd.hasOption("verbose");
		dotOutputDir = cmd.getOptionValue("dotOutputDir", "");
		superDir = dotOutputDir + "/../..";
		// captureLogcatFile = cmd.getOptionValue("captureLogcat", "");
		branchesFile = cmd.getOptionValue("branches", "");
		heuristicsFile = cmd.getOptionValue("heuristics", "");

		// DEBUG
		debug("Input: " + inputApk);
		debug("Output dir: " + outputDir);
		debug("Add tags? " + (addTags ? "yes" : "no"));
		debug("Implicit edges file: " + impFile);
		debug("Generate implicit edges? " + (doImplicit ? "yes" : "no"));
		debug("verbose? " + (verbose ? "yes" : "no"));
		debug("DOT Output dir: " + dotOutputDir);
		if(cmd.hasOption("branches"))
				debug("To-force branches' file: " + branchesFile);
		// log.log(Level.FINE, "Capture logcat file: " + captureLogcatFile);
		debug("Suspicious heuristics: " + heuristicsFile);
		
		//
		if (!cmd.hasOption("branches"))
			System.out.println("Instrumenting APK: Looking for suspicious instructions...");
		else
			System.out.println("Instrumenting APK: Forcing branches...");
	}

	/**
	 * @param args
	 *            defined in getOptions
	 */
	public static void main(String[] args) {
		setOptions(args);

		debug("Initializing SOOT...");
		Settings.initialiseSoot(inputApk, sootOutputDir);

		Pack jtp = PackManager.v().getPack("jtp");

		// Transformation : APK tagging (should be done first)
		if (addTags) {
			Transform taggerTransform = new Transform("jtp.tagger", branchTagger);
			jtp.add(taggerTransform);
		}

		// Transformation : heuristics for suspicious code targeting
		if (!heuristicsFile.isEmpty()) {
			heuristicsInspector = new HeuristicsInspector(heuristicsFile);
			Transform inspectorTransform = new Transform("jtp.heuristics", heuristicsInspector);
			jtp.add(inspectorTransform);
		}

		// Load heuristicsFile
		try {
			JSONParser parser = new JSONParser();
			heuristicJson = (JSONObject) parser.parse(new FileReader(heuristicsFile));
		} catch (Exception e) {
			G.v().out.println("Failed to open or parse " + heuristicsFile);
			e.printStackTrace();
		}

		JSONArray packagesArray = (JSONArray) heuristicJson.get("packages_to_ignore");
		for (Object obj : packagesArray)
			packagesToIgnore.add((String) obj);
		// End loading heuristicsFile

		// Transformation : branch forcing
		if (!branchesFile.isEmpty()) {
			branchForcer = new BranchForcer(branchesFile);
			Transform forceTransform = new Transform("jtp.force", branchForcer);
			jtp.add(forceTransform);
		}

		// Transformation : graph creation
		if (!dotOutputDir.isEmpty()) {
			File dotDir = new File(dotOutputDir);
			if (!dotDir.exists())
				dotDir.mkdirs();

			cfgBuilder = new CfgBuilder();
			Transform cfgTransform = new Transform("jtp.cfgbuilder", cfgBuilder);
			jtp.add(cfgTransform);
		}

		PackManager.v().runPacks();
		PackManager.v().writeOutput();

		debug("Number of processed methods: " + nbrMethods);

		// Logging
		branchTagger.writeInfos();
		if (heuristicsInspector != null) {
			heuristicsInspector.writeTargetsList();
			heuristicsInspector.writeInfos();
		}

		// Post-treatment
		String outputApk = sootOutputDir + inputApk.substring(inputApk.lastIndexOf("/"));
		SignerAligner.signAndAlign(outputApk);

		if (doImplicit && branchesFile.isEmpty() && (!impFile.isEmpty())) {
			long startTime = System.currentTimeMillis();
			ImpGen.v().allSupToFile(superDir + "/allSup.txt");
			ImpGen.v().genInterProcEdges(impFile, superDir + "/genImpEdges.txt");
			long endTime = System.currentTimeMillis();
			debug("Generating implicit edges took " + (endTime - startTime) / 1000 + " seconds");
		}
	}

	public static Boolean is_class_useless(String def_class) {
		for (String packageToIgnore : packagesToIgnore) {
			if (def_class.startsWith(packageToIgnore)) {
				return true;
			}
		}
		return false;
	}

	public static Boolean is_resource_dummy(String methodSignature) {
		if (methodSignature == null)
			methodSignature = "";
		return (methodSignature.split("\\$")[0].endsWith(".R")
				&& (methodSignature.contains("<init>") || methodSignature.contains("<clinit>")));
	}
	
	// Print debug messages only in verbose mode
	public static void debug(String message){
		// If not verbose mode do no thing
		if (!verbose) return;
		
		// Print the message
		System.out.println(message);
	}
}
