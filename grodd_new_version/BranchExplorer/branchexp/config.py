""" Config files handler.

The main section for our config is "branchexp", and then each tool has its own
section. Paths defined in "script" options can be relative paths. The complete
list of options used by BranchExplorer or its sub-components at some point is
in the documentation (or readme).
"""

import configparser
import logging
import os
import sys
from os.path import abspath, dirname, isfile, isdir, join, normpath

log = logging.getLogger("branchexp")

from branchexp.runners.info import VALID_RUNNERS
from branchexp.utils.utils import quit


DEFAULT_CONFIG_FILE = "{0}/config.ini".format(dirname(abspath(__file__)))

ALL_TAGS_FILE = "all_tags.log"
SEEN_TAGS_FILE = "seen_tags.log"
TIMED_TAGS_FILE = "timed_tags.log"
TARGETS_FILE = "targets.json"
ACFG_FILE = "acfg.dot"
BRANCHES_FILE = "to_force.log"
BLARE_FILE = "blare.log"
TRACES_FILE = "traces.log"


def setup(args, config_file = None):
    log.info("Setup environment")
    try:
        config = load_config(config_file or DEFAULT_CONFIG_FILE)
        handle_args(args, config)
        check_config(config)
        set_env_vars(config)
        print_config_digest(config)
    except KeyError as exception:
        quit("An error occurred during config loading, fix your config file: " +
             str(exception))
    return config


def load_config(config_file):
    """ Returns a ConfigParser for the default config file, or for the file
    located at config_file if provided. """
    platform = None
    if sys.platform.startswith("linux"):
        platform = "linux"
    else:
        platform = "macosx"

    config = configparser.ConfigParser({"home": os.environ.get("HOME", "")
                                        , "platform": platform})
    config.read(config_file)

    return config


def handle_args(args, config):
    """ Modify config according to given command-line arguments """
    if args.device:
        config["branchexp"]["device"] = args.device
    if args.device_code:
        config["branchexp"]["device_code"] = args.device_code
    if args.run_type:
        config["branchexp"]["run_type"] = args.run_type
    if args.max_runs:
        config["branchexp"]["max_runs"] = args.max_runs
    if args.output_dir:
        config["branchexp"]["output_dir"] = abspath(args.output_dir)
    if args.context:
        config["branchexp"]["context"] = args.context
    else:
        config["branchexp"]["context"] = ""
    if args.trigger:
        config["branchexp"]["trigger"] = args.trigger
    else:
        config["branchexp"]["trigger"] = ""


def check_config(config):
    """ Check if required config options are present and correct,
    else quit the program. """
    if not config["branchexp"]["run_type"] in VALID_RUNNERS:
        quit( "Invalid run type" )

    suspicious_db = abspath(join( dirname(__file__)
                                , config["branchexp"]["suspicious_db"] ))
    if not isfile(suspicious_db):
        quit("No heuristic JSON database found at " + suspicious_db)
    config["branchexp"]["suspicious_db"] = suspicious_db

    build_tools = join(config["branchexp"]["android_home"],
                       "build-tools",
                       config["branchexp"]["android_tools_version"])
    if not isdir(build_tools):
        quit( "There is no build tools directory at " + build_tools + ".\n" )


def print_config_digest(config):
    log.info( "- Device name: " + config["branchexp"]["device"] + " " +
              "(code: " + config["branchexp"]["device_code"] + ")")
    log.info( "- Run type: " + config["branchexp"]["run_type"] + " " +
              "(limited to " + config["branchexp"]["max_runs"] + " runs)")
    log.info( "- Suspicious heuristics DB: " +
              config["branchexp"]["suspicious_db"] )
    log.info( "- Output directory: " + config["branchexp"]["output_dir"] )


def set_env_vars(config):
    """ Set environment variables used by BranchExplorer or its components. """
    android_home = config["branchexp"]["android_home"]
    tools_version = config["branchexp"]["android_tools_version"]
    build_tools = join(android_home, "build-tools", tools_version)

    os.environ["ANDROID_HOME"] = android_home
    os.environ["PATH"] += ":" + join(android_home, "platform-tools")
    os.environ["PATH"] += ":" + build_tools


def check_tools(working_dir, config):
    """ Check that my tools are there and return them in a dict.

    If some tool has to be removed from this project at some point, we
    should remove its check from here as this function logs an error if
    a tool is missing. This function assumes that the config is sane (= has the
    required sections and options).
    """
    log.debug("Checking tools and environment")

    def sanepath(relative_path):
        return normpath(join(working_dir, relative_path))

    tools = {}

    tools["forcecfi"] = sanepath(config["tools"]["forcecfi_jar"])
    if not isfile(tools["forcecfi"]):
        quit("There is no ForceCFI JAR at " + tools["forcecfi"])

    tools["apktool"] = sanepath(config["tools"]["apktool"])
    if not isfile(tools["apktool"]):
        quit("There is no Apktool script at " + tools["apktool"])

    return tools
