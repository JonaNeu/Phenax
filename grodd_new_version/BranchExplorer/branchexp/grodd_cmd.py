#!/usr/bin/env python3
""" BranchExplorer is the high-level tool that tries to explore specific parts
of code rather than maximizing coverage like regular automatic testing. """

import argparse
import logging
import os
import sys
import time
import datetime

import branchexp.imports
import branchexp.config
from branchexp.explo.simple_explorer import Explorer, explore_apk
from branchexp.utils.utils import quit

log = logging.getLogger("branchexp")
try:
    import coloredlogs
    coloredlogs.install(
        show_hostname=False, show_name=True,
        logger=log,
        level='DEBUG'
    )
except ImportError:
    log.error("Can't import coloredlogs, logs may not appear correctly.")

DESCRIPTION = "Manager for APK instrumentation and branch-forcing."


def main():
    sys.excepthook = on_uncaught_error

    args = setup_args()

    apk = os.path.abspath(args.apk_path)
    if not os.path.isfile(apk):
        quit("The APK provided doesn't exists: " + apk)

    # Print time when processing begins
    time_begin = time.time()
    dt_begin = datetime.datetime.fromtimestamp(time.time()) \
        .strftime('%Y-%m-%d %H:%M:%S')
    print("Begin processing: {} at {}".format(apk, dt_begin))

    config = branchexp.config.setup(args)

    # Setup logging
    level = None
    if config["logging"]["level"] == "verbose":
        level = logging.DEBUG
    elif config["logging"]["level"] == "normal":
        level = logging.INFO
    else:
        log.error("Logging level \"{}\" not defined, setting \"normal\" instead"
                  .format(config["logging"]["level"]))
        level = logging.INFO
    # Check if coloredlogs has been imported
    log.setLevel(level)

    explore_apk(apk, config, time_begin)

    # Print time when processing ends
    time_end = time.time()
    dt_end = datetime.datetime.fromtimestamp(time.time()) \
        .strftime('%Y-%m-%d %H:%M:%S')
    print("Finish processing: {} at {}, it took: {}".format(apk, dt_end,
          str(datetime.timedelta(seconds=(time_end - time_begin)))))


def setup_args():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument("apk_path", type=str,
                        help="path to the APK")
    parser.add_argument("--device", type=str, dest="device",
                        help="name of the device to use")
    parser.add_argument("--device-code", type=str, dest="device_code",
                        help="device code to use")
    parser.add_argument("--run-type", type=str, dest="run_type",
                        help="type of automatic run to do")
    parser.add_argument("--max-runs", type=str, dest="max_runs",
                        help="maximum limit on number of runs")
    parser.add_argument("--output-dir", type=str, dest = "output_dir",
                        help="output directory of run_# subdirs")
    parser.add_argument("--context", type=str, dest = "context",
                        help="to restore a previously saved automaton")
    parser.add_argument("--trigger", type=str, dest = "trigger",
                        help="list of actions/transitions to trigger")

    return parser.parse_args()


def on_uncaught_error(error_type, value, traceback):
    log.error("Uncaught error!")
    sys.__excepthook__(error_type, value, traceback)

    log.error("Killing running Explorers")
    for explorer in Explorer.__all__:
        try:
            if explorer.runner is not None:
                explorer.runner.terminate()
        except Exception as e:
            log.error("Error while killing explorers: " + str(e))
    if error_type is KeyboardInterrupt:
        quit("Program interrupted with Ctrl-C", 3)
    else:
        quit("Exiting after uncaught error.", 1)


if __name__ == "__main__":
    main()
