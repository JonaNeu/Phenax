package instru.graphs;

import instru.Main;

import java.io.File;
import java.util.Map;

import soot.Body;
import soot.BodyTransformer;
import soot.Unit;
import soot.toolkits.graph.BriefUnitGraph;
import soot.toolkits.graph.DirectedGraph;
import soot.toolkits.graph.ExceptionalUnitGraph;
import soot.toolkits.graph.TrapUnitGraph;
import soot.toolkits.graph.pdg.EnhancedUnitGraph;
import soot.util.cfgcmd.CFGToDotGraph;
import soot.util.dot.DotGraph;

/**
 * Generates control-flow graphs (CFGs) in DOT format (Graphviz) for each method.
 */
public class CfgBuilder extends BodyTransformer {

	/**
	 * This enum contains the different Unit graph types Soot can produce.
	 * For more infos, see DirectedCallGraph in Soot javadoc.
	 */
	public enum GraphType { BRIEF, EXCEPTIONAL, ENHANCED, TRAP }
	
	@Override
	protected void internalTransform(Body body, String phase, Map<String, String> options) {
		String bodySignature = body.getMethod().getSignature();
		
		DotGraph graph = bodyToGraph(body);
		graph.setGraphName(bodySignature);
		
		File f = new File(Main.dotOutputDir + "/" + bodySignature + ".dot");
		graph.plot(f.getAbsolutePath());
	}
	
	/**
	 * Create the control-flow graph of body and store it in graphFile as a .dot file.
	 * @param body
	 * @param graphFile
	 */
	public static DotGraph bodyToGraph(Body body) {
		return bodyToGraph(body, GraphType.EXCEPTIONAL);
	}
	
	/**
	 * Create the control-flow graph of body and store it in graphFile.
	 * @param body
	 * @param graphFile
	 * @param graphType GraphType to use
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
		
		CFGToDotGraph graphBuilder = new CFGToDotGraph();
		return graphBuilder.drawCFG(dg, body);
	}

}
