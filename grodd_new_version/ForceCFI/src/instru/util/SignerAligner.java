package instru.util;

import java.io.File;
import java.io.IOException;
import java.lang.ProcessBuilder.Redirect;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;

import instru.Main;

/**
 * Sign and align an APK respectively with jarsigner and zipalign.
 */
public class SignerAligner {
	
	private SignerAligner() {}
	
	/**
	 * Sign an APK with jarsigner
	 * jarsigner needs to be in your PATH.
	 * @param apk Path to the APK
	 */
	public static void sign(String apk) {
		ProcessBuilder pb = new ProcessBuilder(
			"jarsigner",
			"-verbose",
			"-sigalg", "SHA1withRSA",
			"-digestalg", "SHA1", 
			"-keystore", "res/debug.keystore",
			"-storepass", "android",
			"-keypass", "android",
			apk,
			"androiddebugkey"
		);
		pb.redirectErrorStream(true);
		pb.redirectOutput(Redirect.to(new File("/dev/null")));
		try {
			Process p = pb.start();
			if (p.waitFor() == 0)
				Main.debug(apk + " signed with jarsigner.");
			else
				System.err.println("An error occured with jarsigner (is it in your PATH?),"
					+ " check .jarsigner_log.");
		} catch (IOException e) {
			e.printStackTrace();
			return;
		} catch (InterruptedException e) {
			e.printStackTrace();
			return;
		}
	}
	
	/**
	 * Align an APK with zipalign (set to 4 byte alignment). Replace existing APK.
	 * zipalign needs to be in your PATH.
	 * @param apk Path to the APK
	 */
	public static void align(String apk) {
		String apk2 = apk.substring(0, apk.length() - 4) + "-aligned.apk";
		
		ProcessBuilder pb = new ProcessBuilder("zipalign", "-f", "4", apk, apk2);
		pb.redirectErrorStream(true);
		pb.redirectOutput(Redirect.to(new File("/dev/null")));
		try {
			Process p = pb.start();
			if (p.waitFor() == 0)
				Main.debug(apk + " aligned with zipalign.");
			else
				System.err.println("An error occured with zipalign (is it in your PATH?),"
					+ " check .zipalign_log.");
		} catch (IOException e) {
			e.printStackTrace();
			return;
		} catch (InterruptedException e) {
			e.printStackTrace();
			return;
		}
	}
	
	/**
	 * Sign and align an APK. The new APK is stored at the same place but with "-aligned" appended
	 * to its name (before the .apk extension). The unaligned APK is deleted if possible.
	 * @param apk Path to the APK
	 */
	public static void signAndAlign(String apk) {
		sign(apk);
		align(apk);
		Path path = FileSystems.getDefault().getPath(apk);
		try {
			Files.delete(path);
		} catch (IOException e) {
			System.err.println("Could not delete the unaligned APK at " + path.getFileName());
		}
	}
	
}
