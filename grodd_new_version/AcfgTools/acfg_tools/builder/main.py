#!/usr/bin/env python3
""" Perform some operations on Android method CFGs to output a more
comprehensive global app graph. """

import argparse
import os.path
import logging

from acfg_tools.builder.cfg_analyser import CfgAnalyser

DESCRIPTION = "Create a global app graph from CFGs"

log = logging.getLogger("branchexp")


def main():
    argparser = argparse.ArgumentParser(description=DESCRIPTION)
    argparser.add_argument("dots", type=str, help="DOT files directory")
    argparser.add_argument("manifest", type=str, help="app manifest file")
    argparser.add_argument("heuristics_db", type=str, help="JSON db")
    argparser.add_argument("impfile", type=file, help="implicit edges file")
    args = argparser.parse_args()

    if not os.path.isdir(args.dots) or not os.path.isfile(args.manifest):
        print("Unavailable file or directory given.")
        return
    # TODO: update argument list
    generate_acfg(args.dots, args.manifest, args.heuristics_db, args.impfile,
                  (args.impfile is not None))


def generate_acfg(dots, manifest, heuristics, doImplicit, exhaustive_paths,
                  output_dir, suspKeys, paths_out, output_filepath = None):
    """ Generate an ACFG for CFGs in the dots dir, with the app manifest and
    the heuristic db provided. """
    cfg_analyser = CfgAnalyser(dots, manifest, doImplicit, exhaustive_paths,
                               output_dir, heuristics, suspKeys, paths_out)
    cfg_analyser.create_app_graph()
    return cfg_analyser.app_graph.graph

if __name__ == "__main__":
    main()
