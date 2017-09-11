""" Wrapper for some Apktool methods """

import logging
import os
import subprocess

log = logging.getLogger("branchexp")


class Apktool(object):
    """ Interface for Apktool to extract stuff. We just need its ability to
    decode binary XML, namely AXML. """

    def __init__(self, apktool_path):
        self.script = apktool_path

    def extract_resources(self, apk, output_dir):
        """ Extracts resources of apk and returns a subdir of output_dir
        where extracted files are stored. """
        output_dir = os.path.join(output_dir, "apktool")
        extract_command = [self.script, "d", apk, "-s", "-o", output_dir]

        log.debug("Extracting resources of " + apk
                 + " in " + output_dir + " with Apktool.")
        if log.level != logging.DEBUG:
            devnull = open(os.devnull, 'w')
            subprocess.call(extract_command, stdout=devnull)
        else:
            subprocess.call(extract_command)

        return output_dir
