from enum import Enum
import logging
import os
from os.path import abspath, dirname
import subprocess

log = logging.getLogger("branchexp")

from branchexp.utils.utils import quit


class ForceCfi(object):
    """ Interface for the ForceCFI program, as it uses several arguments and
    requires some specific attention.

    Simply instantiate a ForceCfi object and set its attributes to whatever you
    want. Only apk and output_dir are required to execute ForceCFI.
    """

    class Phase(Enum):
        compute_infos = 1
        instrument = 2

    def __init__(self, jar):
        self.jar_path = jar

        self.apk = None
        self.output_dir = None

        self.add_tags = False
        self.graphs_dir = None
        self.heuristics_db = None
        self.branches_file = None

    def execute(self):
        """ Execute ForceCFI, using the informations given. """
        if self.apk is None or self.output_dir is None:
            raise RuntimeError(
                "You must configure at least an APK and an output directory "
                "before starting ForceCfi."
            )

        command = self._generate_command()
        log.info("Starting ForceCFI with command: " + " ".join(command))

        current_dir = os.path.abspath(os.curdir)
        os.chdir(dirname(abspath(self.jar_path)))
        try:
            process = subprocess.Popen(command)
            process.wait()
        except OSError as exception:
            quit("An error occured with ForceCFI: " + str(exception))
        os.chdir(current_dir)

    def _generate_command(self):
        """ Generate an appropriate command with all non-None attributes. """
        command = [
            "java", "-jar", self.jar_path,
            "-inputApk", self.apk,
            "-outputDir", self.output_dir
        ]

        if self.add_tags:
            command += ["-addTags"]
        if self.graphs_dir:
            command += ["-dotOutputDir", self.graphs_dir]
        if self.heuristics_db:
            command += ["-heuristics", self.heuristics_db]
        if self.branches_file:
            command += ["-branches", self.branches_file]

        return command
