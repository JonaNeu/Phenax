#!/usr/bin/env python3
""" Controller for the Android Debug Bridge (adb) Logcat.

If the module is used as a standalone program, the SIGTERMs are captured to
close a bit more properly the thread and subprocess.
"""

__author__ = "jf (original), adrien (inclusion in BranchExplorer)"

import logging
import re
import signal
import subprocess
import threading

log = logging.getLogger("logcatctl")

from branchexp.utils.async_file_reader import AsynchronousFileReader as AFR


LOGCAT_ENTRY_RE = re.compile(
    r"(?P<logtype>\w)/"
    r"(?P<tag>\S+)\s*"
    r"\(\s*(?P<timestamp>\d+)\)"
    r": (?P<message>.*)"
)


class Controller(object):
    """ Controller for the Android Debug Bridge (adb) Logcat. """

    def __init__(self, device = None):
        self.device = device
        self.logcat_process = None
        self.capture = set()
        self.shutdown_flag = threading.Event()

    def start_logcat(self):
        """ Start adb logcat subprocess.

        Actually it calls logcat two times: the first time with the -c flag to
        clear data from possible previous runs, in case of the device hasn't
        been restarted. The second call opens logcat_process, with the correct
        JFL tag filter.

        If a device has been provided, it is passed to the adb command line
        so only one device logs are captured.
        """
        log.info("Starting LogcatController")

        clean_command = ["adb", "logcat", "-c"]
        if self.device is not None:
            clean_command[1:1] = ["-s", self.device.name]
        subprocess.call(clean_command)

        logcat_command = ["adb", "logcat", "JFL:I", "*:S"]
        if self.device is not None:
            logcat_command[1:1] = ["-s", self.device.name]
        self.logcat_process = subprocess.Popen(
            logcat_command,
            stdout = subprocess.PIPE
        )

    def stop_logcat(self):
        """ Stop (send SIGTERM) adb logcat subprocess. """
        log.info("Terminating LogcatController")
        self.shutdown_flag.set()
        self.logcat_process.terminate()
        self.logcat_process.wait()

    def capture_entries(self):
        """ Capture entries from the logcat subprocess.

        Even if it uses an AsynchronousFileReader, this method uses
        busy-waiting to wait for more lines from the subprocess.
        Use self.shutdown_flag.set() to break the loop.

        You can set self.shutdown_flag from another thread, and if that process
        receives a SIGTERM, it will set this flag and exit the loop.
        """
        stdout_reader = AFR(self.logcat_process.stdout)
        stdout_reader.start()

        # Check the queues if we received some output
        # (until there is nothing more to get or we get interrupted).
        while not stdout_reader.eof() and not self.shutdown_flag.is_set():
            for line in stdout_reader.readlines():
                match = LOGCAT_ENTRY_RE.match(line.decode())
                if match:
                    entry = match.groupdict()
                    log.debug(entry["timestamp"] + " : " + entry["message"])
                    self.capture.add(entry["message"])

    def save_capture(self, capture_filepath = "seen_tags.log"):
        """ Save captured tags in capture_file, one tag per line. """
        log.info("Writing capture file (" + str(len(self.capture)) + " entries)")
        with open(capture_filepath, "w") as capture_file:
            for tag in self.capture:
                capture_file.write(tag + "\n")


def sigterm_handler(signum, frame):
    log.info("SIGTERM received")
    controller.shutdown_flag.set()


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)

    global controller
    controller = Controller()
    controller.start_logcat()
    controller.capture_entries()
    controller.stop_logcat()

    controller.save_capture()


if __name__ == "__main__":
    main()
