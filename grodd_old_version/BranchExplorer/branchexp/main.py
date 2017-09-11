#!/usr/bin/env python3
""" BranchExplorer is the high-level tool that tries to explore specific parts
of code rather than maximizing coverage like regular automatic testing. """

import argparse
import logging
import os
import sys

log = logging.getLogger("branchexp")

try:
    import coloredlogs
    coloredlogs.install(
        show_hostname = False, show_name = True,
        level = logging.DEBUG
    )
except ImportError:
    logging.error("Can't import coloredlogs, logs may not appear correctly.")
    logging.basicConfig(level = logging.DEBUG)

import branchexp.imports

import branchexp.config
from branchexp.explo.explorer import Explorer, explore_apk
from branchexp.utils.utils import quit

DESCRIPTION = "Manager for APK instrumentation and branch-forcing."


def main():
    sys.excepthook = on_uncaught_error

    args = setup_args()

    apk = os.path.abspath(args.apk_path)
    if not os.path.isfile(apk):
        quit("The APK provided doesn't exists: " + apk)

    config = branchexp.config.setup(args)
    explore_apk(apk, config)


def setup_args():
    parser = argparse.ArgumentParser(description = DESCRIPTION)

    parser.add_argument("apk_path", type = str,
        help = "path to the APK")
    parser.add_argument("--device", type = str, dest = "device",
        help = "name of the device to use")
    parser.add_argument("--device-code", type = str, dest = "device_code",
        help = "device code to use")
    parser.add_argument("--run-type", type = str, dest = "run_type",
        help = "type of automatic run to do")
    parser.add_argument("--max-runs", type = str, dest = "max_runs",
        help = "maximum limit on number of runs")
    parser.add_argument("--output-dir", type = str, dest = "output_dir",
        help = "output directory of run_# subdirs")

    return parser.parse_args()


def on_uncaught_error(error_type, value, traceback):
    log.critical("Uncaught error!")
    sys.__excepthook__(error_type, value, traceback)

    log.info("Killing running Explorers")
    for explorer in Explorer.__all__:
        try:
            if explorer.runner is not None:
                explorer.runner.terminate()
        except Exception as e:
            log.error("Error while killing explorers: " + str(e))

    quit("Exiting after uncaught error.")


if __name__ == "__main__":
    main()
