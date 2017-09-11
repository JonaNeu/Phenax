package instru.graphs;

import instru.Settings;

import java.io.IOException;
import java.util.Collections;

import org.xmlpull.v1.XmlPullParserException;

import soot.G;
import soot.Scene;
import soot.SootMethod;
import soot.jimple.infoflow.android.SetupApplication;
import soot.jimple.toolkits.callgraph.CallGraph;
import soot.options.Options;

public class CallGraphInterface {
	
	private SetupApplication app;
	private CallGraph cg;
	
	private CallGraphInterface() {}
	private static CallGraphInterface singleton = new CallGraphInterface();
	public static CallGraphInterface v() { return singleton; }
	
	public void setup(String platforms, String apk) {
		app = new SetupApplication(platforms, apk);
		try {
			app.calculateSourcesSinksEntrypoints(Settings.infoflowDataFile);
		} catch (IOException | XmlPullParserException e) {
			G.v().out.println( "Failed to initialized sources and sink from " +
			                   Settings.infoflowDataFile );
			e.printStackTrace();
		}
		
		// This throws an exception ;(
		SootMethod dummyMain = app.getEntryPointCreator().createDummyMain();
		Options.v().set_main_class(dummyMain.getSignature());
		Scene.v().setEntryPoints(Collections.singletonList(dummyMain));
		
		Options.v().setPhaseOption("cg.spark", "on");
		cg = Scene.v().getCallGraph();
	}
	
	public void generate() {

		G.v().out.println("CG size: " + cg.size());
		G.v().out.println(cg.toString());
		
	}
	
}
