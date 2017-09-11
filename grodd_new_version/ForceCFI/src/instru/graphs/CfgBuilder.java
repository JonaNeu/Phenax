package instru.graphs;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Map;

import instru.Main;
import soot.Body;
import soot.BodyTransformer;
import soot.Scene;
import soot.Type;
import soot.Unit;
import soot.toolkits.graph.BriefUnitGraph;
import soot.toolkits.graph.DirectedGraph;
import soot.toolkits.graph.ExceptionalUnitGraph;
import soot.toolkits.graph.TrapUnitGraph;
import soot.toolkits.graph.pdg.EnhancedUnitGraph;
import soot.util.dot.DotGraph;

/**
 * Generates control-flow graphs (CFGs) in DOT format (Graphviz) for each
 * method.
 */
public class CfgBuilder extends BodyTransformer {

	/**
	 * This enum contains the different Unit graph types Soot can produce. For
	 * more info, see DirectedCallGraph in Soot javadoc.
	 */
	public enum GraphType {
		BRIEF, EXCEPTIONAL, ENHANCED, TRAP
	}

	@Override
	protected void internalTransform(Body body, String phase, Map<String, String> options) {
		String bodySignature = body.getMethod().getSignature();
		// if (bodySignature.contains("android.support") ||
		// bodySignature.contains(".R$"))
		if (Main.is_class_useless(body.getMethod().getDeclaringClass().toString())
				|| Main.is_resource_dummy(body.getMethod().getSignature()))
			return;

		if (Main.doImplicit) {
			ImpGen.v().addMethodSignature(body.getMethod());
			ImpGen.v().setSup(body.getMethod().getDeclaringClass());
			//ImpGen.v().setSup(Scene.v().getSootClass(body.getMethod().getReturnType().toString()));
			for (Type t : body.getMethod().getParameterTypes()) {
				ImpGen.v().setSup(Scene.v().getSootClass(t.toString()));
			}
		}

		DotGraph graph = bodyToGraph(body);
		graph.setGraphName(bodySignature);

		String filename = Main.dotOutputDir + "/" + bodySignature + ".dot";
		if ((bodySignature + ".dot").length() > 255)
			filename = Main.dotOutputDir + "/" + getShortFileName(bodySignature + ".dot");

		File f = new File(filename);
		graph.plot(f.getAbsolutePath());
	}

	String getShortFileName(String longFileName) {
		// test if file name is greater than 255 characters
		if (longFileName.length() <= 255)
			return longFileName;

		File file = new File(Main.outputDir + "/" + "short_file_names.txt");
		if (!file.exists()) {
			try {
				file.createNewFile();
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}

		String shortFileName = "";
		String lastLine = "";
		// Read the last short file name
		try (BufferedReader br = new BufferedReader(new FileReader(Main.outputDir + "/" + "short_file_names.txt"))) {
			String line;
			while ((line = br.readLine()) != null) {
				// process the line.
				lastLine = line;
			}
		} catch (FileNotFoundException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		} catch (IOException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}

		if (!lastLine.isEmpty()) {
			String lastfileName = lastLine.split("\t")[0];
			int lastInt = Integer.parseInt(lastfileName.substring(lastfileName.lastIndexOf('/') + 1, lastfileName.lastIndexOf('.')));
			shortFileName = Main.dotOutputDir + "/" + (++lastInt) + ".dot";
		} else {
			shortFileName = Main.dotOutputDir + "/" + "1.dot";
		}
		// Append the new file name
		try {
			BufferedWriter out = new BufferedWriter(
					new FileWriter(Main.outputDir + "/" + "short_file_names.txt", true));
			String appendLine = shortFileName + "\t" + Main.dotOutputDir + "/" + longFileName + "\n";
			//System.out.print("Appending line: " + appendLine);
			out.write(appendLine);
			out.close();
		} catch (IOException e) {
			// exception handling left as an exercise for the reader
		}
		return shortFileName.substring(shortFileName.lastIndexOf('/') + 1, shortFileName.length());
	}

	/**
	 * Create the control-flow graph of body and store it in graphFile as a .dot
	 * file.
	 * 
	 * @param body
	 * @param graphFile
	 */
	public static DotGraph bodyToGraph(Body body) {
		return bodyToGraph(body, GraphType.EXCEPTIONAL);
	}

	/**
	 * Create the control-flow graph of body and store it in graphFile.
	 * 
	 * @param body
	 * @param graphFile
	 * @param graphType
	 *            GraphType to use
	 */
	public static DotGraph bodyToGraph(Body body, GraphType graphType) {
		DirectedGraph<Unit> dg = null;
		switch (graphType) {
		case BRIEF:
			dg = new BriefUnitGraph(body);
			break;
		case EXCEPTIONAL:
			dg = new ExceptionalUnitGraph(body);
			break;
		case ENHANCED:
			dg = new EnhancedUnitGraph(body);
			break;
		case TRAP:
			dg = new TrapUnitGraph(body);
			break;
		default:
			System.err.println("Unknown GraphType in bodyToGraph");
			System.exit(-1);
		}

		// CFGToDotGraph graphBuilder = new CFGToDotGraph();
		RichGraph graphBuilder = new RichGraph();
		return graphBuilder.drawCFG(dg, body);
	}

}
