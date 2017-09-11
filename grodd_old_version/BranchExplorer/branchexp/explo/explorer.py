import logging
import os
from os.path import join, abspath, basename, dirname, isfile, splitext
import shutil

log = logging.getLogger("branchexp")

from acfg_tools.builder.main import generate_acfg
from acfg_tools.exec_path_finder.acfg import AppGraph as PathFinderAcfg
from acfg_tools.exec_path_finder.main import get_path_infos_for_alert
from manifest_parser.manifest import Manifest

from branchexp.android.device import Device
from branchexp.config import ( check_tools, ALL_TAGS_FILE, SEEN_TAGS_FILE
                             , TARGETS_FILE, ACFG_FILE, BRANCHES_FILE )
from branchexp.explo.forcecfi import ForceCfi
from branchexp.explo.stats import RunStats
from branchexp.explo.target_selector import TargetSelector
from branchexp.runners.base_runner import RunInfos
from branchexp.runners.manual import ManualRunner
from branchexp.runners.monkey import MonkeyUiExerciserRunner
from branchexp.runners.grodd import GroddRunner
from branchexp.utils.apktool import Apktool
from branchexp.utils.utils import execute_in, quit
from branchexp.android.blare import init_blare


@execute_in(directory = dirname(abspath(__file__)))
def explore_apk(apk, my_config):
    explorer = Explorer(apk, my_config)
    explorer.setup()
    explorer.process_apk()


class Explorer(object):
    """ Class in charge of calling the tagger, the automatic tester and everyone
    at the right moment and with the right data.

    Several properties are available to access useful directories for the
    current run without having to compute its paths yourself.

    Attributes:
        working_dir: global working directory, where that script is
        original_apk: path to the clean APK given during instanciation
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

    def __init__(self, apk, my_config):
        """ Create a new Explorer, ready to work on that apk. """
        type(self).__all__.add(self)

        self.working_dir = abspath(dirname(__file__))

        self.original_apk = apk
        self.manifest = None
        self.config = my_config

        self.targets = []
        self.acfg = None

        self.device = None
        self.run_id = 0
        self.run_params = {}
        self.runner = None
        self.every_seen_tags = { "method": set(), "branch": set() }

        self.tools = {}

    def __del__(self):
        type(self).__all__.remove(self)

    @property
    def output_dir(self):
        return abspath(self.config["branchexp"]["output_dir"])
    @property
    def run_directory(self):
        return join(self.output_dir, "run_{}".format(self.run_id))
    @property
    def apk_directory(self):
        return join(self.run_directory, "apk")
    @property
    def dots_directory(self):
        return join(self.run_directory, "dot")

    @property
    def all_tags_file(self):
        return join(self.run_directory, ALL_TAGS_FILE)
    @property
    def seen_tags_file(self):
        return join(self.run_directory, SEEN_TAGS_FILE)
    @property
    def targets_file(self):
        return join(self.run_directory, TARGETS_FILE)
    @property
    def branches_file(self):
        return join(self.run_directory, BRANCHES_FILE)
    @property
    def tagged_apk(self):
        return join( self.apk_directory
                   , splitext(basename(self.original_apk))[0] + "-aligned.apk" )

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

        while self.run_id < max_runs:
            os.makedirs(self.run_directory)

            self.monitor_run()
            if self.run_params.get("stop", False):
                log.info("Nothing interesting found for another run, stopping.")
                break

            self.run_id += 1

        log.info("The processing of " + self.original_apk + " is done.")

    def clean(self):
        """ Remove files left by an execution. """
        log.info("Cleaning files of previous sessions")
        shutil.rmtree(self.output_dir, ignore_errors = True)
        os.makedirs(self.output_dir)

    def load_manifest(self):
        """ Load the Manifest from the APK in self.manifest, using Apktool. """
        apktool = Apktool(self.tools["apktool"])
        apktool_dir = apktool.extract_resources( self.original_apk
                                               , self.output_dir )

        manifest_path = join(apktool_dir, "AndroidManifest.xml")
        if not isfile(manifest_path):
            quit( "Couldn't find a manifest file at " + manifest_path + ". "
                  "Did ManifestParser worked properly?" )
        self.manifest = Manifest(manifest_path)

    def monitor_run(self):
        """ Do one monitored run of the APK, handle the instrumentation
        and the runners. """
        log.info((" Monitoring run #" + str(self.run_id) + " ").center(40, "~"))

        if self.run_id == 0:
            self.instrument_apk(ForceCfi.Phase.compute_infos)
            self.load_targets()

        if self.run_id >= len(self.targets):
            log.info("No more targets to execute!")
            self.run_params["stop"] = True
            return

        self.find_run_parameters()
        self.instrument_apk(ForceCfi.Phase.instrument)
        self.run_apk()

        self.compute_run_stats()

    def instrument_apk(self, phase):
        """ Run ForceCFI to tag the APK, generate DOTs and targets,
        and force some branches if necessary. """
        log.info("Instrumenting APK")

        forcecfi = self._get_forcecfi(phase)
        forcecfi.execute()

        if not isfile(self.tagged_apk):
            quit( "Tagged APK unavailable at " + self.tagged_apk + ". "
                  "Did ForceCFI stopped correctly?" )
        if ( phase == ForceCfi.Phase.compute_infos
             and not isfile(self.targets_file) ):
            quit( "No targets file available at " + self.targets_file + "." )

    def _get_forcecfi(self, phase):
        """ Prepare a ForceCfi object with adapted parameters for this run. """
        forcecfi = ForceCfi(self.tools["forcecfi"])
        forcecfi.apk = self.original_apk
        forcecfi.output_dir = self.run_directory
        forcecfi.add_tags = True

        if phase == ForceCfi.Phase.compute_infos:
            forcecfi.graphs_dir = self.dots_directory
            forcecfi.heuristics_db = self.config["branchexp"]["suspicious_db"]
        elif phase == ForceCfi.Phase.instrument:
            if "to_force" in self.run_params:
                self._prepare_branches_file()
                forcecfi.branches_file = self.branches_file

        return forcecfi

    def _prepare_branches_file(self):
        """ Write the branches in a file known by the ForceCfi program. """
        with open(self.branches_file, "w") as branches_file:
            for branch in self.run_params.get("to_force", []):
                branches_file.write(branch + "\n")

    def load_targets(self):
        """ Load targets computed by ForceCFI. """
        selector = TargetSelector(self.targets_file)
        max_targets = int(self.config["branchexp"]["max_runs"])
        targets = selector.get_selected_targets(max_targets)

        self.targets = targets

    def find_run_parameters(self):
        """ Find parameters for the next run, like an entry point and branches
        to force by using stats from the last run.

        Returns:
            a dict with appropriate options: entry_point, to_force, monitor_tags
        """
        log.info("Finding next run parameters")
        run_params = {}

        target = self._get_next_target()
        alert = self._get_next_alert(target)
        path_infos = self._get_exec_path_infos(alert)

        run_params["target"] = str(target)
        run_params["alert"] = str(alert)
        run_params["entry_point"] = path_infos["entry_point"]
        run_params["to_force"] = path_infos["branches"]
        run_params["monitor_tags"] = [ path_infos["nearest_tag"] ]

        log.info("Parameters for the next run:")
        for key in run_params:
            log.info("- " + key + ": " + str(run_params[key]))

        self.run_params = run_params

    def _get_next_target(self):
        """ Get a target to focus on during the next run. """
        assert self.run_id < len(self.targets)
        next_target = self.targets[self.run_id]
        return next_target

    def _get_next_alert(self, target):
        """ Get an alert to focus on from this target. """
        main_alert = max(target.alerts, key = lambda alert: alert.score)
        return main_alert

    def _get_exec_path_infos(self, alert):
        """ Use ACFG tools to find informations about a possible execution path
        to this alert. """
        if not self.acfg:
            acfg_path = join(self.output_dir, ACFG_FILE)
            acfg = generate_acfg( self.dots_directory, self.manifest
                                , self.config["branchexp"]["suspicious_db"]
                                , output_filepath = acfg_path )
            self.acfg = acfg

        log.info("Focusing on alert: " + str(alert))

        path_finder_acfg = PathFinderAcfg()
        path_finder_acfg.graph = self.acfg
        path_finder_acfg.is_valid = True

        path_infos = get_path_infos_for_alert(path_finder_acfg, alert)

        return path_infos

    def run_apk(self):
        """ Use an automatic runner to perform an automatic run of the APK.

        The APK is sent to the runner so it can be automatically run on a clean
        environment, with some system for UI events automation. Tags are
        collected by the LogcatController. See the runner module for more
        details about the automatic runs.
        """
        log.info("Running APK on device")

        run_infos = self._get_run_infos()

        run_type = self.config["branchexp"]["run_type"]
        if   run_type == "manual":
            self.runner = ManualRunner(run_infos)
        elif run_type == "monkey":
            self.runner = MonkeyUiExerciserRunner(run_infos)
        elif run_type == "grodd":
            self.runner = GroddRunner(run_infos)

        self.runner.run()
        
        if not isfile(self.seen_tags_file):
            quit( "No capture file found at " + self.seen_tags_file + ". "
                  "You want to check if the logcatctl was correctly started." )

        init_blare(self.runner.device)
        self.runner = None

    def _get_run_infos(self):
        """ Generate an appropriate RunInfos instance for the next run. """
        run_infos = RunInfos()

        run_infos.apk = self.tagged_apk
        run_infos.manifest = self.manifest
        run_infos.entry_point = self.run_params["entry_point"]
        run_infos.tools = self.tools
        run_infos.device = self.device
        run_infos.output_dir = self.run_directory

        return run_infos

    def compute_run_stats(self):
        """ Compute statistics from the last run. """
        run_stats = RunStats(self.all_tags_file, self.seen_tags_file)

        run_seen_tags = run_stats.stats["tags"]["seen"]
        self.every_seen_tags["method"] |= run_seen_tags["method"]
        self.every_seen_tags["branch"] |= run_seen_tags["branch"]

        run_stats.analyse_targeted_execution( self.run_params
                                            , self.every_seen_tags )

        run_stats.compute_global_stats(self.every_seen_tags)

        run_stats.log_digest()
        run_stats.write_json(join(self.run_directory, "stats.json"))
