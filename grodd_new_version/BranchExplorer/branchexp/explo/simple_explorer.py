import logging
import os
from os.path import join, abspath, basename, dirname, isfile, splitext
import shutil
import datetime
import time
import sys
import collections
from tempfile import mkstemp
import multiprocessing
from shutil import move
from os import remove, close

from acfg_tools.builder.main import generate_acfg
from acfg_tools.exec_path_finder.acfg import AppGraph as PathFinderAcfg
from acfg_tools.exec_path_finder.main import get_path_info_for_alert
from acfg_tools.exec_path_finder.path_finder import PathFinder
from manifest_parser.manifest import Manifest

from branchexp.android.device import Device
from branchexp.config import (check_tools, ALL_TAGS_FILE, SEEN_TAGS_FILE,
                              TIMED_TAGS_FILE, TARGETS_FILE, ACFG_FILE,
                              BRANCHES_FILE)
from branchexp.explo.forcecfi import ForceCfi
from branchexp.explo.stats import RunStats
from branchexp.explo.target_selector import TargetSelector
from branchexp.runners.base_runner import RunInfo
from branchexp.runners.manual import ManualRunner
from branchexp.runners.monkey import MonkeyUiExerciserRunner
from branchexp.runners.grodd import GroddRunner
from branchexp.runners.grodd2 import GroddRunner2
from branchexp.utils.apktool import Apktool
from branchexp.utils.utils import execute_in, quit
from branchexp.android.blare import init_blare

try:
    from progressbar import ProgressBar

    use_progressbar = True
except ImportError:
    use_progressbar = False

log = logging.getLogger("branchexp")
NUM_CORES = len(os.sched_getaffinity(0))


@execute_in(directory=dirname(abspath(__file__)))
def explore_apk(apk, my_config, time_begin):
    explorer = Explorer(apk, my_config, time_begin)
    explorer.setup()
    explorer.process_apk()


class Explorer(object):
    """ Class in charge of calling the tagger, the automatic tester and everyone
    at the right moment and with the right data.

    Several properties are available to access useful directories for the
    current run without having to compute its paths yourself.

    Attributes:
        working_dir: global working directory, where that script is
        original_apk: path to the clean APK given during instantiation
        manifest: the Manifest object extracted from the original APK
        config: ConfigParser with all given options
        targets: list of suspicious targets identified for that application
        acfg: ACFG computed from the original APK
        run_id: counter for the runs we performed (starting at run 0)
        run_params: parameters for the next run, as a dict
        runner: reference to the Runner being used during a run, in case we have
            to shut it down. Set to None when no run is being performed.
        every_seen_tags: dict with 2 keys, "method" and "branch", both being
            sets of tags (str) seen during at least one previous run.
        tools: dict of paths to tools that we use
    """

    __all__ = set()

    def __init__(self, apk, my_config, time_begin):
        """ Create a new Explorer, ready to work on that apk. """
        type(self).__all__.add(self)

        self.working_dir = abspath(dirname(__file__))

        self.original_apk = apk
        self.manifest = None
        self.config = my_config

        self.targets = []
        self.all_targets = []
        self.all_suspicious_keys = set()
        self.acfg = None

        self.device = None
        self.run_id = 0
        self.run_params = {}
        self.runner = None
        self.every_seen_tags = {"method": set(), "branch": set()}

        self.tools = {}
        self.monitored_tags = set()
        self.executed_tags = set()
        self.doImplicit = int(self.config["branchexp"]["doImplicit"])
        self.exhaustive_paths = \
            int(self.config["branchexp"]["exhaustive_paths"])
        self.wait_for_internet = \
            int(self.config["branchexp"]["wait_for_internet"])
        self.start_time = time.time()
        self.paths = {}
        self.real_paths_list = []
        self.cfg_completed = False
        self.last_run_stats = None
        self.time_begin = time_begin

        if self.exhaustive_paths:
            with open(self.config["branchexp"]["paths_out"], "a") as f:
                f.write("Apk: {}\n".format(apk))
                f.write("Date: {}\n".format(datetime.datetime.now().
                                            strftime('%Y-%m-%d %H:%M:%S.%f')[
                                            :-3]))
                f.write("Size: {}\n"
                        .format(os.path.
                                getsize(self.original_apk)))

    # def __del__(self):
    #     type(self).__all__.remove(self)

    @property
    def output_dir(self):
        return abspath(self.config["branchexp"]["output_dir"])
    @property
    def run_directory(self):
        return join(self.output_dir, "run_{}".format(self.run_id))

    @property
    def ref_run_directory(self):
        return join(self.output_dir, "run_0")

    @property
    def apk_directory(self):
        return join(self.run_directory, "apk")
    @property
    def dots_directory(self):
        return join(self.run_directory, "dot")

    @property
    def ref_dots_directory(self):
        return join(self.ref_run_directory, "dot")

    @property
    def all_tags_file(self):
        return join(self.run_directory, ALL_TAGS_FILE)
    @property
    def seen_tags_file(self):
        return join(self.run_directory, SEEN_TAGS_FILE)
    @property
    def timed_tags_file(self):
        return join(self.run_directory, TIMED_TAGS_FILE)
    @property
    def targets_file(self):
        return join(self.run_directory, TARGETS_FILE)
    @property
    def branches_file(self):
        return join(self.run_directory, BRANCHES_FILE)
    @property
    def tagged_apk(self):
        return self.original_apk

    def setup(self):
        """ Setup the Explorer by loading tools and resources. """
        self.clean()
        self.tools = check_tools(self.working_dir, self.config)
        self.load_manifest()
        self.device = Device(self.config["branchexp"]["device"],
                             self.config["branchexp"]["device_code"],
                             self.config["branchexp"]["twrp_backup"])

    def process_apk(self):
        """ Explore interesting branches of an APK through the whole
        targeting and instrumentation process. """
        max_runs = int(self.config["branchexp"]["max_runs"])

        #TODO remove this
        # self.run_id = 1

        while self.run_id < max_runs:
            os.makedirs(self.run_directory)

            self.monitor_run()
            if self.run_params.get("stop", False):
                log.info("Nothing interesting found for another run, stopping.")
                break

            self.run_id += 1

            # TODO: remove or comment this bloc
            exit()

        log.debug("The processing of " + self.original_apk + " is done.")
        self.print_results()

    def clean(self):
        """ Remove files left by an execution. """
        log.debug("Cleaning files of previous sessions")
        shutil.rmtree(self.output_dir, ignore_errors=True)
        os.makedirs(self.output_dir)

    def load_manifest(self):
        """ Load the Manifest from the APK in self.manifest, using Apktool. """
        apktool = Apktool(self.tools["apktool"])
        apktool_dir = apktool.extract_resources(self.original_apk
                                                , self.output_dir)

        manifest_path = join(apktool_dir, "AndroidManifest.xml")
        if not isfile(manifest_path):
            quit("Couldn't find a manifest file at " + manifest_path + ". "
                 "Did ManifestParser worked properly?")
        self.manifest = Manifest(manifest_path)

    def monitor_run(self):
        """ Do one monitored run of the APK, handle the instrumentation
        and the runners. """
        print("### Monitoring run #{}".format(self.run_id))


        self.run_apk()
        self.run_params["stop"] = True



    def count_alert_types(self):
        count_alerts = {}
        for target in self.all_targets:
            for alert in target.alerts:
                if alert.category not in count_alerts:
                    count_alerts[alert.category] = 1
                else:
                    count_alerts[alert.category] += 1
        return count_alerts


    def find_run_parameters(self):
        """ Find parameters for the next run, like an entry point and branches
        to force by using stats from the last run.

        Returns:
            a dict with appropriate options: entry_point, to_force, monitor_tags
        """
        log.debug("Finding next run parameters")
        run_params = {}

        log.debug("Parameters for this run:")
        for key in run_params:
            log.debug("- " + key + ": " + str(run_params[key]))

        print("Target: {}".format(run_params["target"]))
        print("Entry point: {}".format(run_params["entry_point"]))
        print("Branch(es) to force: {}".format(len(run_params["to_force"])))

        self.run_params = run_params

    def _get_next_target(self):
        """ Get a target to focus on during the next run. """
        assert self.run_id <= len(self.targets)
        next_target = self.targets[self.run_id - 1]
        return next_target



    def run_apk(self):
        """ Use an automatic runner to perform an automatic run of the APK.

        The APK is sent to the runner so it can be automatically run on a clean
        environment, with some system for UI events automation. Tags are
        collected by the LogcatController. See the runner module for more
        details about the automatic runs.
        """
        log.debug("Running APK on device...")

        run_info = self._get_run_info()

        run_type = self.config["branchexp"]["run_type"]
        if run_type == "manual":
            self.runner = ManualRunner(run_info)
        elif run_type == "monkey":
            self.runner = MonkeyUiExerciserRunner(run_info)
        elif run_type == "grodd":
            self.runner = GroddRunner(run_info)
        elif run_type == "grodd2":
            self.runner = GroddRunner2(run_info)

        if int(self.config["branchexp"]["use_blare"]) == 1:
            init_blare(self.runner.device)

        self.runner.run()
        
        if not isfile(self.seen_tags_file):
            quit("No capture file found at " + self.seen_tags_file + ". "
                 "You want to check if the logcatctl was correctly started.")

        self.runner = None

    def _get_run_info(self):
        """ Generate an appropriate RunInfo instance for the next run. """
        run_info = RunInfo()

        run_info.apk = self.tagged_apk
        run_info.manifest = self.manifest
        run_info.tools = self.tools
        run_info.device = self.device
        run_info.output_dir = self.run_directory
        run_info.use_blare = int(self.config["branchexp"]["use_blare"])
        run_info.doImplicit = self.doImplicit
        run_info.uninstall = int(self.config["branchexp"]["uninstall"])
        run_info.wait_for_internet = self.wait_for_internet
        run_info.context = self.config["branchexp"]["context"]
        run_info.trigger = self.config["branchexp"]["trigger"]

        return run_info

    def compute_run_stats(self):
        """ Compute statistics from the last run. """
        run_stats = RunStats(self.all_tags_file, self.seen_tags_file,
                             self.run_id)

        run_seen_tags = run_stats.stats["tags"]["seen"]
        self.every_seen_tags["method"] |= run_seen_tags["method"]
        self.every_seen_tags["branch"] |= run_seen_tags["branch"]

        monitored, executed = run_stats.analyse_targeted_execution(
            self.run_params, self.every_seen_tags)
        self.monitored_tags |= monitored
        self.executed_tags |= executed

        run_stats.compute_global_stats(self.every_seen_tags)

        run_stats.log_digest()
        run_stats.write_json(join(self.run_directory, "stats.json"))

        return run_stats

    def print_results(self):
        log.debug("Final results:")
        log.debug("- Global monitored tags: {}".format(self.monitored_tags))
        log.debug("- Global hit tags: {}".format(self.executed_tags))
        commun = self.monitored_tags & self.executed_tags
        if len(self.monitored_tags) != 0:
            percent = len(commun) * 100 / len(self.monitored_tags)
        else:
            percent = 0
        if self.last_run_stats is not None:
            self.last_run_stats.print_final()
        print("- Suspicious code hit: {}%".format(percent))
        self.write_results(percent, "/tmp/results.txt")

    def write_results(self, coverage, out_file):
        dt = datetime.datetime.fromtimestamp(time.time())\
            .strftime('%Y-%m-%d %H:%M:%S')
        end_time = time.time()
        f_exec = str(datetime.timedelta(seconds=(end_time -
                                                 self.start_time)))
        if self.config["branchexp"]["run_type"] == "monkey":
            analyse_type = "MONKEY"
        elif self.doImplicit and\
                int(self.config["branchexp"]["force"]) == 1:
            analyse_type = "FEM"
        elif not self.doImplicit and\
                int(self.config["branchexp"]["force"]) == 1:
            analyse_type = "FORCENOEM"
        elif not self.doImplicit and\
                int(self.config["branchexp"]["force"]) == 0:
            analyse_type = "NOFORCE"
        else:
            analyse_type = "MIXED"
        not_detected = ""
        if not self.monitored_tags:
            not_detected = "\t>>> NOT DETECTED"
        with open(out_file, "a") as f:
            f.write("{}\t{}%\t{}\t{}\t{}{}\n".
                    format(self.original_apk, coverage, dt,
                           analyse_type, f_exec, not_detected))
