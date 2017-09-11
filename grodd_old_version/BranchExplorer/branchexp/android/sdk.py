import logging
import os
import re
import subprocess

log = logging.getLogger("branchexp")


def send_command(command, blocking = True, stdin = None, stdout = None):
    """ Send a command in a subprocess.

    If blocking is True, return the return value and binary output.
    """
    if stdin is None:
        stdin = subprocess.PIPE
    if stdout is None:
        stdout = subprocess.PIPE

    log.debug("Sending command: " + " ".join(command))
    process = subprocess.Popen(command, stdin = stdin, stdout = stdout)

    result = None
    output = ""
    if blocking:
        result = process.wait()
        output = process.stdout.read()
    return result, output


def flash(device, partition, image):
    """ Flash an image to a partition using fastboot. """
    if not partition in ("system", "userdata", "boot"):
        raise Exception(partition + " is not a valid partition")
    if not os.path.isfile(image):
        raise Exception(image + " is not a file")

    log.debug("Flashing partition " + partition + " with image " + image)
    flash_command = ["flash", partition, image]
    result, _ = device.send_command(flash_command, tool = "fastboot")
    if result != 0:
        raise Exception(
            "Error when flashing device {}.\n{}".format(device.name, result)
        )


def get_package_name(apk):
    """ Get the package name from this APK, using aapt. """
    aapt_command = ["aapt", "dump", "badging", apk]
    try:
        aapt_output = subprocess.check_output(aapt_command).decode()
    except (OSError, subprocess.CalledProcessError) as exception:
        log.error("Failed to use aapt: " + str(exception))
        return None

    for line in aapt_output.splitlines():
        if line.startswith("package:"):
            return re.search(r"name='([\.\w]+)'", line).group(1)

    log.error("Unexpected output from aapt.")
    return None
