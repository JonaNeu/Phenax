""" Tools for installing AndroBlare and associated tools.

Note that I merged most of these methods from the now dead BlareRunner folder.
It was quickly written Python 2, now rewritten as Python 3 but it has not been
tested, so some errors will probably show up here as for some reason I can't
install it on my test phone.
"""

import logging


log = logging.getLogger("branchexp")

def init_blare(device):
    """ Flash the device and init blare tags

    This requires a root access on the device when using adb shell.
    """
    # log.info("Initializing Blare ...")
    # device.twrp_flash()
    # device.wait_until_ready()

    # # Ignore these two services when doing DIFT with AndroBlare
    # log.info("Remounting the filesystem ...")
    # cmd = ["shell", "mount",
    #        "-o", "rw,remount",
    #        "/system"]
    # device.send_command(cmd)
    # # tag_file(device, "/system/bin/servicemanager", 0)
    # # tag_file(device, "/system/bin/surfaceflinger", 0)

    # device.send_command(["reboot"])
    # device.wait_until_ready()


def tag_file(device, file_location, tag=99):
    """ Set Blare tag on the file at file_location. """
    log.info("Setting Blare tag {} on {}".format(tag, file_location))
    try:
        device.send_command(["shell", "setinfo", file_location, str(tag)])
    except OSError as exception:
        log.error("Can't setinfo on " + file_location + ": " + str(exception))
