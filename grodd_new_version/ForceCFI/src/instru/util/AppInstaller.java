package instru.util;

import java.io.File;
import java.io.IOException;
import java.lang.ProcessBuilder.Redirect;

/**
 * Wrapper for APK installation.
 */
public class AppInstaller {

	private AppInstaller() {}
	
	/**
	 * Install an APK on a connected device or an emulator.
	 * Won't work if there's more or less than exactly one device, virtual or not.
	 * adb needs to be in your PATH.
	 * @param apk Path to the APK
	 */
	public static void install(String apk) {
		ProcessBuilder pb = new ProcessBuilder("adb", "install", "-r", apk);
		pb.redirectErrorStream(true);
		pb.redirectOutput(Redirect.to(new File(".adb_log")));
		try {
			Process p = pb.start();
			if (p.waitFor() == 0)
				System.out.println(apk + " installed.");
			else
				System.out.println("An error occured with adb (is it in your PATH?),"
					+ " check .adb_log.");
		} catch (IOException e) {
			e.printStackTrace();
			return;
		} catch (InterruptedException e) {
			e.printStackTrace();
			return;
		}
	}
	
}
