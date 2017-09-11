#from duplicity.backends.dpbxbackend import command
from enum import Enum
import logging
import os
from os.path import abspath, dirname
import subprocess

from branchexp.utils.utils import quit

log = logging.getLogger("branchexp")


class ForceCfi(object):
    """ Interface for the ForceCFI program, as it uses several arguments and
    requires some specific attention.

    Simply instantiate a ForceCfi object and set its attributes to whatever you
    want. Only apk and output_dir are required to execute ForceCFI.
    """

    class Phase(Enum):
        compute_info = 1
        instrument = 2
        # add option here

    def __init__(self, jar):
        self.jar_path = jar

        self.apk = None
        self.output_dir = None

        self.add_tags = False
        self.graphs_dir = None
        self.heuristics_db = None
        self.branches_file = None
        self.doImplicit = False
        self.verbose = False
        if log.level == logging.DEBUG:
            self.verbose = True

    def execute(self):
        """ Execute ForceCFI, using the information given. """
        if self.apk is None or self.output_dir is None:
            raise RuntimeError(
                "You must configure at least an APK and an output directory "
                "before starting ForceCfi."
            )

        command = self._generate_command()
        log.debug("Starting ForceCFI with command: " + " ".join(command))

        current_dir = os.path.abspath(os.curdir)
        os.chdir(dirname(abspath(self.jar_path)))
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       bufsize=1)
            for line in iter(process.stdout.readline, b''):
                self._grep(line.decode("utf-8"))
            process.stdout.close()
            process.wait()
        except OSError as exception:
            quit("An error occurred with ForceCFI: " + str(exception))
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
        if self.imp_edges_file:
            command += ["-impFile", self.imp_edges_file]
        if self.doImplicit:
            command += ["-doImplicit"]
        if self.verbose:
            command += ["-verbose"]

        return command

    def _grep(self, line):
        """
        :type line: str
        """
        start = [
            "Transforming",
            "Ignoring",
            "Warning",
            "get",
            "Using",
            "WARNING",
            "array",
            "Writing",
            "do",
            "warning:"
        ]
        end =[
            "jarsigner.\n",
            "zipalign.\n"
        ]
        for s in start:
            if line.startswith(s):
                return
        for e in end:
            if line.endswith(e):
                return
        print(line, end="", flush=True)
