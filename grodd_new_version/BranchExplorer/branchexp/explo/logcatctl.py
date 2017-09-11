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

log = logging.getLogger("branchexp")

from branchexp.utils.async_file_reader import AsynchronousFileReader as AFR


LOGCAT_ENTRY_RE = re.compile(
    r"(?P<logtype>\w)/"
    r"(?P<tag>\S+)\s*"
    r"\(\s*(?P<timestamp>\d+)\)"
    r": (?P<message>.*)"
)

# I/JFL     ( 6450): BRANCHN14878
# 08-20 03:12:21.349 I/JFL     ( 6231): BEGINN26490

# Reg Ex to match the Signature traces
LOGCAT_ENTRY_SIG_RE = re.compile(
    r"(?P<timestamp>[0-9\-: .]+)\s*"
    r"(?P<logtype>\w)/"
    r"(?P<tag>\S+AL)\s*"
    r"\(\s*(?P<pid>\d+)\)"
    r": (?P<message>.*)"
)


class Controller(object):
    """ Controller for the Android Debug Bridge (adb) Logcat. """

    def __init__(self, device = None):
        self.device = device
        self.logcat_process = None
        self.capture = [] #set()
        self.timed_tags = []
        self.shutdown_flag = threading.Event()

        # added by me 
        self.traces = []

    def start_logcat(self):
        """ Start adb logcat subprocess.

        Actually it calls logcat two times: the first time with the -c flag to
        clear data from possible previous runs, in case of the device hasn't
        been restarted. The second call opens logcat_process, with the correct
        JFL tag filter.

        If a device has been provided, it is passed to the adb command line
        so only one device logs are captured.
        """
        log.debug("Starting LogcatController")

        clean_command = ["adb", "logcat", "-c"]
        if self.device is not None:
            clean_command[1:1] = ["-s", self.device.name]
        subprocess.call(clean_command)

    
        # TODO: add my custom tag "JFL-AL:I"
        logcat_command = ["adb", "logcat", "-v", "time", "JFL:I", "JFL-AL:I" "*:S"]
        if self.device is not None:
            logcat_command[1:1] = ["-s", self.device.name]
        self.logcat_process = subprocess.Popen(
            logcat_command,
            stdout=subprocess.PIPE
        )

    def stop_logcat(self):
        """ Stop (send SIGTERM) adb logcat subprocess. """
        log.debug("Terminating LogcatController")
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
        first = True
        while not stdout_reader.eof() and not self.shutdown_flag.is_set():
            for line in stdout_reader.readlines():
                match = LOGCAT_ENTRY_RE.match(line.decode())
                if match:
                    entry = match.groupdict()
                    # log.debug(entry["timestamp"] + " : " + entry["message"])
                    self.capture.append(entry["message"])
                    self.timed_tags.append({"timestamp": entry["timestamp"],
                                            "message": entry["message"]})
                # added by me
                match = LOGCAT_ENTRY_SIG_RE.match(line.decode())
                if match:
                    entry = match.groupdict()
                    # log.debug(entry["timestamp"] + " : " + entry["message"])
                    
                    # TODO: add the timestamp
                    self.traces.append(entry["timestamp"]+ " " + entry["message"])


    def save_capture(self, capture_filepath="seen_tags.log",
                     timed_filepath="timed_tags.log", traces_filepath="traces.log"):
        """ Save captured tags in capture_file, one tag per line. """
        log.debug("Writing capture file (" + str(len(self.capture)) + " entries)")
        with open(capture_filepath, "w") as capture_file:
            for tag in self.capture:
                capture_file.write(tag + "\n")
        with open(timed_filepath, "w") as timed_file:
            for tag in self.timed_tags:
                timed_file.write(tag["timestamp"] + " " + tag["message"] + "\n")

        # added by me
        
        with open(traces_filepath, "w") as traces_file:
            for trace in self.traces:
                traces_file.write(trace + "\n")



def sigterm_handler(signum, frame):
    log.debug("SIGTERM received")
    controller.shutdown_flag.set()


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)

    global controller
    controller = Controller()
    controller.start_logcat()
    log.debug("Looping on UI")
    controller.capture_entries()
    controller.stop_logcat()

    controller.save_capture()


if __name__ == "__main__":
    main()
