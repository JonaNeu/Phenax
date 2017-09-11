package instru;

import java.util.Collections;

import soot.G;
import soot.Scene;
import soot.SootClass;
import soot.options.Options;

public class Settings {
	
	private static boolean SOOT_INITIALIZED = false;
	public final static String androidJar = "./lib/android.jar";
	public final static String androidPlatforms = "./res/android-platforms";
	public final static String infoflowDataFile = "./res/SourcesAndSinks.txt";
	
	public static boolean isInitialized() {
		return SOOT_INITIALIZED;
	}
	
	public static void initialiseSoot(String apk, String output) {
		if (SOOT_INITIALIZED)
			return;
		G.reset();
		
		Options.v().set_allow_phantom_refs(true);
//		Options.v().set_whole_program(true);
		Options.v().set_prepend_classpath(true);
//		Options.v().set_validate(true);
		Options.v().set_force_overwrite(true);
		
		Options.v().set_output_format(Options.output_format_dex);
		Options.v().set_process_dir(Collections.singletonList(apk));
		Options.v().set_android_jars(androidPlatforms);
//		Options.v().set_force_android_jar(androidJar);
		Options.v().set_src_prec(Options.src_prec_apk);
		
		Options.v().set_output_dir(output);
		
		Options.v().set_soot_classpath(androidJar);
		
		Scene.v().addBasicClass("android.util.Log", SootClass.SIGNATURES);
		Scene.v().loadNecessaryClasses();

		SOOT_INITIALIZED = true;
	}
	
}
