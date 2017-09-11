import re, json
from Utils import *
from grodd_new_version.ManifestParser.manifest_parser.manifest import Manifest

class Extractor():

    def __init__(self):
        self.all_traces_features = []
        self.total_invoke_count = 0
        self.virtual_invoke_count = 0
        self.special_invoke_count = 0
        self.send_sms_count = 0
        self.startActivity_count = 0
        self.startservice_count = 0
        self.onCreate_count = 0
        self.onStart_count = 0
        self.onResume_count = 0
        self.onPause_count = 0
        self.onStop_count = 0
        self.onDestroy_count = 0
        self.onReceive_count = 0
        self.binary_category = 0
        self.dynamic_category = 0
        self.crypto_category = 0
        self.network_category = 0
        self.telephony__category = 0
        self.accounts_category = 0
        self.bluetooth_category = 0
        self.gps_category = 0
        self.nfc_category = 0
        self.os_category = 0
        self.io_category = 0
        self.recording_category = 0
        self.display_category = 0
        self.content = 0
        self.context = 0
        self.database = 0
        self.camera = 0
        self.toast = 0


    def load_log_file (self, filepath):
        result = []
        with open(filepath, "r") as file:
            for line in file:
                result.append(line.rstrip('\n'))
        return result

    ############################################################
    # Main method to extract all features
    ############################################################
    def extract_traces_features(self, traces_file_path):
        traces = self.load_log_file(traces_file_path)

        for trace in traces:
            self.extract_special_invokes(trace)
            self.extract_virtual_invokes(trace)
            self.extract_total_invokes(trace)
            self.extract_send_sms_methods(trace)
            self.extract_startActivity_methods(trace)
            self.extract_startService_methods(trace)
            self.extract_onCreate_methods(trace)
            self.extract_onStart_methods(trace)
            self.extract_onResume_methods(trace)
            self.extract_onPause_methods(trace)
            self.extract_onStop_methods(trace)
            self.extract_onDestroy_methods(trace)
            self.extract_onReceive_methods(trace)
            self.extract_binary_category(trace)
            self.extract_dynamic_category(trace)
            self.extract_crypto_category(trace)
            self.extract_network_category(trace)
            self.extract_telephony_category(trace)
            self.extract_accounts_category(trace)
            self.extract_bluetooth_category(trace)
            self.extract_gps_category(trace)
            self.extract_nfc_category(trace)
            self.extract_os_category(trace)
            self.extract_io_category(trace)
            self.extract_recording_category(trace)
            self.extract_display_category(trace)
            self.extract_content(trace)
            self.extract_context(trace)
            self.extract_database(trace)
            self.extract_camera(trace)
            self.extract_toast(trace)


        self.all_traces_features.append(self.total_invoke_count)
        self.all_traces_features.append(self.virtual_invoke_count)
        self.all_traces_features.append(self.special_invoke_count)
        self.all_traces_features.append(self.send_sms_count)
        self.all_traces_features.append(self.startActivity_count)
        self.all_traces_features.append(self.startservice_count)
        self.all_traces_features.append(self.onCreate_count)
        self.all_traces_features.append(self.onStart_count)
        self.all_traces_features.append(self.onResume_count)
        self.all_traces_features.append(self.onPause_count)
        self.all_traces_features.append(self.onStop_count)
        self.all_traces_features.append(self.onDestroy_count)
        self.all_traces_features.append(self.onReceive_count)
        self.all_traces_features.append(self.binary_category)
        self.all_traces_features.append(self.dynamic_category)
        self.all_traces_features.append(self.crypto_category)
        self.all_traces_features.append(self.network_category)
        self.all_traces_features.append(self.telephony__category)
        self.all_traces_features.append(self.accounts_category)
        self.all_traces_features.append(self.bluetooth_category)
        self.all_traces_features.append(self.gps_category)
        self.all_traces_features.append(self.nfc_category)
        self.all_traces_features.append(self.os_category)
        self.all_traces_features.append(self.io_category)
        self.all_traces_features.append(self.recording_category)
        self.all_traces_features.append(self.display_category)
        self.all_traces_features.append(self.content)
        self.all_traces_features.append(self.context)
        self.all_traces_features.append(self.database)
        self.all_traces_features.append(self.camera)
        self.all_traces_features.append(self.toast)

        # we could also try to compare the size of the previous traces file and this one and store the difference

        return self.all_traces_features

    def extract_targets_features(self, targets_file_path):
        features = []

        # the number of elements in the "alerts" part
        alerts_count = 0
        score_sum = 0

        with open(targets_file_path) as data_file:
            data = json.load(data_file)
            try:
                # the number of times "alerts" appear in the file
                features.append(len(data))

                for i in data:
                    for j in i["alerts"]:
                        alerts_count += 1
                    score_sum += i["score"]

            except Exception:
                pass

            features.append(alerts_count)
            features.append(score_sum)

        return features

    def extract_to_force_features(self, to_force_file_path):
        file_data = self.load_log_file(to_force_file_path)
        count = 0

        for _ in file_data:
            count += 1

        return count

    def extract_stats_features(self, stats_file_path):
        features = []

        with open(stats_file_path) as data_file:
            data = json.load(data_file)

            try:
                features.append(len(data["tags"]["all"]["method"]))
                features.append(len(data["tags"]["all"]["cond"]))

                features.append(len(data["tags"]["seen"]["method"]))
                features.append(len(data["tags"]["seen"]["branch"]))

                features.append(data["targeted"]["num_executed"])
                features.append(data["targeted"]["num_targeted"])
                features.append(data["targeted"]["coverage"])

                features.append(data["coverage"]["method"])
                features.append(data["coverage"]["branch"])

            except Exception:
                pass

        return features



    def extract_manifest_file_features(self, manifest_file_path):
        manifest = Manifest(manifest_file_path)

        return manifest.get_numerical_features()

    def extract_total_invokes(self, trace):
        if re.search("invoke", trace):
            self.total_invoke_count += 1

    def extract_special_invokes(self, trace):
        if re.search("specialinvoke", trace):
            self.special_invoke_count += 1

    def extract_virtual_invokes(self, trace):
        if re.search("virtualinvoke", trace):
            self.virtual_invoke_count += 1

    def extract_send_sms_methods(self, trace):
        if re.search("sendTextMessage", trace):
            self.send_sms_count += 1

    def extract_startActivity_methods(self, trace):
        if re.search("startActivity", trace):
            self.startActivity_count += 1

    def extract_startService_methods(self, trace):
        if re.search("startService", trace):
            self.startservice_count += 1

    def extract_onCreate_methods(self, trace):
        if re.search("onCreate", trace):
            self.onCreate_count += 1

    def extract_onStart_methods(self, trace):
        if re.search("onStart", trace):
            self.onStart_count += 1

    def extract_onResume_methods(self, trace):
        if re.search("onResume", trace):
            self.onResume_count += 1

    def extract_onPause_methods(self, trace):
        if re.search("onPause", trace):
            self.onPause_count += 1

    def extract_onStop_methods(self, trace):
        if re.search("onStop", trace):
            self.onStop_count += 1

    def extract_onDestroy_methods(self, trace):
        if re.search("onDestroy", trace):
            self.onDestroy_count += 1

    def extract_onReceive_methods(self, trace):
        if re.search("onReceive", trace):
            self.onReceive_count += 1



    def extract_binary_category(self, trace):
        if re.search("java.lang.Runtime", trace) or re.search("java.lang.Process", trace) or \
                re.search("java.lang.ProcessBuilder", trace) or re.search("java.lang.System", trace) or \
                re.search("org.apache.commons.exec", trace) or re.search("org.apache.commons.launcher", trace) or \
                re.search("android.os.Process", trace):
            self.binary_category += 1

    def extract_dynamic_category(self, trace):
        if re.search("dalvik.system.BaseDexClassLoader", trace) or re.search("dalvik.system.PathClassLoader", trace) or \
                re.search("dalvik.system.DexClassLoader", trace) or re.search("dalvik.system.DexFile", trace):
            self.dynamic_category += 1

    def extract_crypto_category(self, trace):
        if re.search("javax.crypto", trace) or re.search("java.security.spec", trace) or \
                re.search("org.apache.commons.crypto", trace):
            self.crypto_category += 1

    def extract_network_category(self, trace):
        if re.search("java.net.Socket", trace) or re.search("java.net.ServerSocket", trace) or \
                re.search("java.net.HttpURLConnection", trace) or re.search("java.net.JarURLConnection", trace) or \
                re.search("java.net.URL", trace) or re.search("org.apache.commons.net", trace) or \
                re.search("org.apache.http", trace) or re.search("org.apache.commons.mail", trace) or \
                re.search("android.webkit", trace) or re.search("java.net.ssl", trace) or \
                re.search("java.net.HttpCookie", trace) or re.search("android.app.DownloadManager", trace) or \
                re.search("android.net.Network", trace) or re.search("android.net.wifi.WifiManager", trace):
            self.network_category += 1

    def extract_telephony_category(self, trace):
        if re.search("android.telephony.TelephonyManager", trace):
            self.telephony__category += 1

    def extract_accounts_category(self, trace):
        if re.search("android.accounts.AccountManager", trace):
            self.accounts_category += 1

    def extract_bluetooth_category(self, trace):
        if re.search("android.bluetooth.BluetoothManager", trace):
            self.bluetooth_category += 1

    def extract_gps_category(self, trace):
        if re.search("android.location.LocationManager", trace) or re.search("android.location.LocationProvider", trace):
            self.gps_category += 1

    def extract_nfc_category(self, trace):
        if re.search("android.nfc.NfcManager", trace):
            self.nfc_category += 1

    def extract_os_category(self, trace):
        if re.search("android.os", trace) or re.search("android.content.pm.PackageInstaller", trace) or \
                re.search("android.os.PowerManager", trace):
            self.os_category += 1

    def extract_io_category(self, trace):
        if re.search("java.io.DataInput", trace) or re.search("java.io.DataOutput", trace):
            self.io_category += 1

    def extract_recording_category(self, trace):
        if re.search("android.media.AudioRecord", trace) or re.search("android.media.MediaRecorder", trace):
            self.recording_category += 1

    def extract_display_category(self, trace):
        if re.search("android.hardware.display.DisplayManager", trace):
            self.display_category += 1

    def extract_content(self, trace):
        if re.search("android.content.ContentResolver", trace):
            self.content += 1

    def extract_context(self, trace):
        if re.search("android.content.ContextWrapper", trace):
            self.context += 1

    def extract_database(self, trace):
        if re.search("android.database", trace):
            self.database += 1

    def extract_camera(self, trace):
        if re.search("android.hardware.Camera", trace):
            self.camera += 1

    def extract_toast(self, trace):
        if re.search("android.widget.Toast", trace):
            self.toast += 1

