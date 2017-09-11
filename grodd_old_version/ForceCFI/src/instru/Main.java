package instru;

import instru.force.BranchForcer;
import instru.graphs.CfgBuilder;
import instru.heuristics.HeuristicsInspector;
import instru.tags.BranchTagger;
import instru.util.SignerAligner;

import java.io.File;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.GnuParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

import soot.G;
import soot.Pack;
import soot.PackManager;
import soot.Transform;

/**
 * Parse given args, then perform several Soot transformations: tagging, graph creation and
 * branch forcing.
 */
public class Main {

	public static String inputApk = "";
	public static String outputDir = "";
	public static String sootOutputDir = "";
	public static boolean addTags = false;
//	public static String captureLogcatFile = "";
	public static String dotOutputDir = "";
	public static String branchesFile = "";
	public static String heuristicsFile = "";
	
	public static BranchTagger branchTagger = new BranchTagger();
	public static BranchForcer branchForcer;
	public static CfgBuilder cfgBuilder;
	public static HeuristicsInspector heuristicsInspector;
	
	/** Parse options from command line data. */
	private static void setOptions(String[] args) {
		Options options = new Options();
		
		Option input = new Option(
			"inputApk", true, "The apk file to parse."
		);
		input.setRequired(true);
		options.addOption(input);
		
		Option output = new Option(
			"outputDir", true, "The output dir for the new apk to produce."
		);
		output.setRequired(true);
		options.addOption(output);
		
		Option addTagsOption = new Option(
			"addTags", false, "Add method and branch tags"
		);
		options.addOption(addTagsOption);
		
//		Option captureLogcat = new Option(
//			"captureLogcat", true, "The capture of the logcat trace."
//		);
//		options.addOption(captureLogcat);
		
		Option dotOutput = new Option(
				"dotOutputDir", true, "The output dir for the dot graphs (computes dot files)."
			);
		options.addOption(dotOutput);
			
		Option branches = new Option(
			"branches", true, "A file containing branch names to force"
		);
		options.addOption(branches);
		
		Option heuristics = new Option(
			"heuristics", true, "A JSON file containing heuristics for suspicious code targeting"
		);
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
		System.out.println("Input: " + inputApk);
		
		outputDir = cmd.getOptionValue("outputDir", "");
		sootOutputDir = outputDir + "/apk";
		System.out.println("Output dir: " + outputDir);
		
		addTags = cmd.hasOption("addTags");
		System.out.println("Add tags? " + (addTags ? "yes" : "no"));
		
		dotOutputDir = cmd.getOptionValue("dotOutputDir", "");
		System.out.println("DOT Output dir: " + dotOutputDir);
		
//		captureLogcatFile = cmd.getOptionValue("captureLogcat", "");
//		System.out.println("Capture logcat file: " + captureLogcatFile);
		
		branchesFile = cmd.getOptionValue("branches", "");
		System.out.println("Branches to force list: " + branchesFile);
		
		heuristicsFile = cmd.getOptionValue("heuristics", "");
		System.out.println("Suspicious heuristics: " + heuristicsFile);
	}
	
	/**
	 * @param args defined in getOptions
	 */
	public static void main(String[] args) {
		setOptions(args);
		
		System.out.println("Initializing SOOT...");
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

		// Logging
		branchTagger.writeInfos();
		if (heuristicsInspector != null) {
			heuristicsInspector.writeTargetsList();
			heuristicsInspector.writeInfos();
		}
		
		// Post-treatment
		String outputApk = sootOutputDir + inputApk.substring(inputApk.lastIndexOf("/"));
		SignerAligner.signAndAlign(outputApk);
	}
	
}
