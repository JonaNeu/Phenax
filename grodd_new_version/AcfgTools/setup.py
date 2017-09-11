#!/usr/bin/env python3

from distutils.core import setup

setup(
    name="ACFG Tools",
    version="0.1.0",
    description="Application Control-Flow Graphs builder and analyser",

    author="Adrien Abraham",
    author_email="adrien.abraham@pistache.land",

    packages=[ "acfg_tools"
             , "acfg_tools.builder"
             , "acfg_tools.exec_path_finder" ]
)