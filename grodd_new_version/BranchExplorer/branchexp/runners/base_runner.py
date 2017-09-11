""" Tools for automatically run an APK. """

import logging
import os.path
import subprocess
import threading
import time

log = logging.getLogger("branchexp")

from branchexp.android.blare import tag_file
from branchexp.android.sdk import get_package_name
from branchexp.config import SEEN_TAGS_FILE, BLARE_FILE, TIMED_TAGS_FILE, TRACES_FILE
from branchexp.explo.logcatctl import Controller


class RunInfo(object):
    """ Container class for Runner info. """

    def __init__(self):
        self.apk = None
        self.manifest = None
        self.entry_point = None
        self.tools = None
        self.device = None
        self.output_dir = None
        self.uninstall = 0
        self.context = None
        self.trigger = None


class Runner(object):
    """ Abstract class for an application runner.

    Use start_logcat() and stop_logcat() to grab the logcat entries tagged with
    JFL during the run.

    Attributes:
        apk: path to the APK to run
        tools: tools from an Explorer instance
        run_process: subprocess used to run the APK.
            It can be a subprocess.Popen or a pexpect.spawn.
        logcatctl_process: subprocess of the logcat controller
        shutdown_flag: if set, the runner will try to shutdown itself
    """

    def __init__(self, info):
        """ This constructor should be called by every subclass of Runner.

        Args:
            info: a RunInfo object with appropriate data for this run.
        """
        self.apk = info.apk
        self.manifest = info.manifest
        self.entry_point = info.entry_point
        self.tools = info.tools
        self.device = info.device
        self.output_dir = info.output_dir
        self.use_blare = info.use_blare

        self.package_name = get_package_name(self.apk)

        self.run_process = None
        self.logcatctl = None
        self.shutdown_flag = threading.Event()
        self.blare_logger = None
        self.uninstall = info.uninstall
        self.wait_for_internet = info.wait_for_internet


    @property
    def capture_file(self):
        return os.path.join(self.output_dir, SEEN_TAGS_FILE)

    @property
    def timed_file(self):
        return os.path.join(self.output_dir, TIMED_TAGS_FILE)

    @property
    def blare_log(self):
        return os.path.join(self.output_dir, BLARE_FILE)

    # added by me
    @property
    def traces_file(self):
        return os.path.join(self.output_dir, TRACES_FILE)

    def run(self):
        """ Perform the application run.

        The class Runner doesn't provide a working run() method but subclasses
        do. You also probably want to call prepare_run before and
        clean_after_run after the call to this method, or inside it.
        """
        raise NotImplementedError("Use a subclass of Runner.")

    def prepare_run(self):
        """ Utility to prepare the device for the run.

        It's here that we should flash the device, install Blare and its tools,
        ensure that the app to run isn't already running, etc.
        """

        self.device.wait_until_ready()
        self.device.wake_device()
        self.device.app_manager.kill_app(self.package_name)

        if self.use_blare == 1:
            self.start_blare_logger(self.blare_log)

        self.device.app_manager.uninstall_app(self.package_name)

        if self.wait_for_internet:
            log.info("You have {} second(s) to enable Internet on the device "
                     "{}".format(self.wait_for_internet, self.device.name))
            time.sleep(self.wait_for_internet)

        self.device.install_apk(self.apk)

        if self.use_blare == 1:
            self.trace_apk()

    def clean_after_run(self):
        """ Stop things created during prepare_run once the run is done. """
        self.device.app_manager.kill_app(self.package_name)
        if self.use_blare == 1:
            self.stop_blare_logger()
        # TODO: add introspy switch to config.ini
        self.save_introspy_db(self.package_name)

        # Uninstall the app after the run, to avoid flashing the device
        # To disable that, go to the config file and set "uninstall" to 0
        if self.uninstall:
            self.device.app_manager.uninstall_app(self.package_name)

    def start_logcat(self):
        """ Start Logcat in a subprocess. """
        self.logcatctl = Controller(device = self.device)
        self.logcatctl.start_logcat()

        # The capture is a semi busy-waiting loop, so it has to be started in
        # another thread.
        capture_thread = threading.Thread(
            target = self.logcatctl.capture_entries
        )
        capture_thread.daemon = True
        capture_thread.start()

        log.debug("LogcatController is running.")

    def stop_logcat(self):
        """ Stop the logcat subprocess. """
        self.logcatctl.stop_logcat()
        self.logcatctl.save_capture(self.capture_file, self.timed_file, self.traces_file)
        self.logcatctl = None

    def start_blare_logger(self, output_file = None):
        """ Store Blare log in output """
        if output_file is None:
            output = subprocess.PIPE
        else:
            output = open(output_file, "w")

        grep_command = [ "adb", "-s", self.device.name
                       , "shell", "grep", "BLARE", "/proc/kmsg" ]
        self.blare_logger = subprocess.Popen(grep_command, stdout = output)

    def stop_blare_logger(self):
        """ Stop logging Blare log """
        self.blare_logger.terminate()

    def terminate(self):
        """ Terminate all running subprocesses. """
        if self.run_process is not None:
            self.run_process.terminate()
        if self.logcatctl is not None:
            self.stop_logcat()
        if self.blare_logger is not None:
            self.stop_blare_logger()

    def save_introspy_db(self, pkg):
        data_dir = self.device.get_data_dir(pkg)
        db = "{0}/databases/introspy.db".format(data_dir)
        cmd = ["pull", db, "{0}/introspy.db".format(self.output_dir)]
        self.device.send_command(cmd)

    def trace_apk(self, pkg = None):
        """ Mark the application to be dynamically analyzed
        Analyzers are AndroBlare and Introspy
        """
        apk_location = None
        data_dir = None
        if pkg is None:
            apk_location = self.device.get_apk_location(self.package_name)
            data_dir = self.device.get_data_dir(self.package_name)
        else:
            apk_location = self.device.get_apk_location(pkg)
            data_dir = self.device.get_data_dir(pkg)

        if data_dir is None:
            log.error("Could not find data directory")
        if apk_location is None:
            log.error("Could not find the APK location")

        # Introspy
        if not (data_dir is None):
            cmd = ["shell",
                   "echo",
                   "GENERAL CRYPTO,KEY,HASH,FS,IPC,PREF,URI,SSL,WEBVIEW,CUSTOM"
                   "HOOKS,_ STACK TRACES",
                   ">",
                   "{0}/introspy.config".format(data_dir)]
            self.device.send_command(cmd)
        else:
            log.error("Could not find data directory")

        # AndroBlare
        if not (apk_location is None):
            tag_file(self.device, apk_location)
        else:
            log.error("Could not find the APK location")
