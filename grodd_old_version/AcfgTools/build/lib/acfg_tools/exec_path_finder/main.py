#!/usr/bin/env python3
""" Find execution paths to targets from an ACFG. """

import argparse
import logging as log
import os.path

from acfg_tools.exec_path_finder.acfg import AppGraph
from acfg_tools.exec_path_finder.path_finder import PathFinder
from acfg_tools.exec_path_finder.targets import generate_target_list

DESCRIPTION = "Execution path finder"


def main():
    argparser = argparse.ArgumentParser(description = DESCRIPTION)
    argparser.add_argument("acfg", type = str, help = "Application CFG")
    argparser.add_argument("targets", type = str, help = "targets JSON list")
    args = argparser.parse_args()

    if not os.path.isfile(args.acfg) or not os.path.isfile(args.targets):
        print("Unavailable file or directory given.")
        return

    log.info("Importing the first alert of the first target.")

    app_graph = AppGraph()
    app_graph.load_dot(args.acfg)

    target_list = generate_target_list(args.targets)
    alert = target_list[0].alerts[0]

    get_path_infos_for_alert(app_graph, alert)


def get_path_infos_for_alert(app_graph, alert):
    path_finder = PathFinder(app_graph)
    path_infos = path_finder.process_alert(alert)
    return path_infos


if __name__ == "__main__":
    main()
