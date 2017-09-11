""" Main class for CFG handling and analysis. """

import json
import os

try:
    from progressbar import ProgressBar
    USE_PROGRESSBAR = True
except ImportError:
    USE_PROGRESSBAR = False

from acfg_tools.builder.app_graph import AppGraph
from acfg_tools.builder.method_cfg import MethodCfg
from acfg_tools.builder.utils import quit, separate_output


class CfgAnalyser(object):
    """ Perform some operations on CFGs to create a comprehensive app graph. """

    def __init__(self, dot_dir, manifest, heuristics_file):
        self.method_cfgs = {}
        self.wrong_graph_files = []
        self.app_graph = None
        self.manifest = manifest
        self.heuristics = None

        self.load_dots(dot_dir)
        self.load_signatures(heuristics_file)

    @separate_output
    def load_dots(self, dot_dir):
        """ Load all the method CFGs in the DOT files in dot_dir. """
        if not os.path.isdir(dot_dir):
            quit(dot_dir + " unavailable.")

        dot_file_iterator = os.listdir(dot_dir)
        if USE_PROGRESSBAR:
            progress = ProgressBar()
            dot_file_iterator = progress(dot_file_iterator)

        for dot_file in dot_file_iterator:
            if not os.path.splitext(dot_file)[1] == ".dot":
                continue
            full_path = os.path.join(dot_dir, dot_file)
            self.load_dot(full_path)

        if self.wrong_graph_files:
            print( "\nThe following DOT files couldn't be loaded:\n"
                   + "\n".join(self.wrong_graph_files) )

    def load_dot(self, dot_filepath):
        method_cfg = MethodCfg(dot_filepath)
        if method_cfg.is_valid:
            self.method_cfgs[method_cfg.soot_signature] = method_cfg
        else:
            self.wrong_graph_files.append(dot_filepath)

    @separate_output
    def load_signatures(self, sigs_path):
        with open(sigs_path, "r") as sigs_file:
            self.heuristics = json.load(sigs_file)

    @separate_output
    def create_app_graph(self):
        """ Merges the method CFG in a single, big CFG for the whole app. """
        if not self.method_cfgs or self.manifest is None:
            raise CfgAnalysisError(
                "You have to load the method CFGs with load_dots and load the "
                "manifest with load_manifest before creating an app graph"
            )

        self.app_graph = AppGraph(self.manifest)
        self.app_graph.generate(self.method_cfgs, self.heuristics)

    @separate_output
    def write_app_graph(self, path = None):
        self.app_graph.write_dot(path)


class CfgAnalysisError(Exception):
    pass
