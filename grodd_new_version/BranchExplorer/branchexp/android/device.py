import logging
import sys
import os
import time
import subprocess
from os.path import join as join
from acfg_tools.builder.utils import quit
import branchexp.android.sdk as sdk
from branchexp.android.device_ui import DeviceUi
from branchexp.android.device_app_manager import DeviceAppManager

log = logging.getLogger("branchexp")

# Events that may be useful when executing an application
# http://stackoverflow.com/questions/7789826/adb-shell-input-events
# http://developer.android.com/reference/android/view/KeyEvent.html
# Used to unlock screen
MENU_BUTTON_CODE = 82
POWER_BUTTON_CODE = 26


class Device(object):
    """ Interface for an Android device (real or emulated). """

    def __init__(self, name, image_name, backup_dir="."):
        self.name = name
        self.image_name = image_name
        self.backup_dir = backup_dir
        self.ui = DeviceUi(self)
        self.app_manager = DeviceAppManager(self)

    def send_command(self, command, tool="adb", blocking=True
                     , stdin=None, stdout=None):
        """ Send a command to this device (by default through ADB). """
        tool_command = [tool, "-s", self.name] + command
        return sdk.send_command(
            tool_command, blocking=blocking,
            stdin=stdin, stdout=stdout
        )

    def send_key_event(self, event_code):
        """ Send an event of integer value 'event_code' to the device. """
        event_command = ["shell", "input", "keyevent", str(event_code)]
        return self.send_command(event_command)

    def wait_until_ready(self, mode="adb"):
        """ Wait until device shows up in ADB and is fully booted. """
        sys.stdout.flush()

        log.debug("Waiting for " + self.name + " to be ready")
        log.debug("Waiting for " + self.name + " to be available")
        while not self.is_available(mode=mode):
            time.sleep(2)

        log.debug("Waiting for " + self.name + " to be fully booted")
        while not self.is_booted():
            time.sleep(2)

        print("Device " + self.name + " is ready.")

    def is_available(self, mode="adb"):
        """ Check if device appears in ADB or fastboot devices """
        check_command = list()
        if (mode == "recovery"):
            check_command.append("adb")
        else:
            check_command.append(mode)
        check_command.append("devices")
        _, output = sdk.send_command(check_command)
        for line in output.decode().splitlines():
            if line.startswith(self.name):
                if ((mode == "adb" and line.endswith("device"))
                    or (mode == "fastboot" and line.endswith("fastboot"))
                        or (mode == "recovery" and line.endswith("recovery"))):
                    return True
        return False

    def is_booted(self):
        """ Check if an available device has completed its boot. """
        getprop_command = ["shell", "getprop", "sys.boot_completed"]
        _, output = self.send_command(getprop_command)
        for line in output.decode().splitlines():
            if line.strip("\r\n") == "1":
                return True
        return False

    def remount_system_rw(self):
        """ Remount /system partition of this device in read&write mode. """
        log.debug("Remount /system in RW mode")
        remount_command = ["shell", "mount", "-o", "rw,remount", "/system"]
        self.send_command(remount_command)

    def wake_device(self):
        """ Send some key events to wakeup the screen if it isn't on. """
        if not self.is_screen_on():
            self.send_key_event(POWER_BUTTON_CODE)
            time.sleep(2)
        self.send_key_event(MENU_BUTTON_CODE)

    def is_screen_on(self):
        """ Check if the device screen is on (= shows something). """
        dumpsys_command = ["shell", "dumpsys", "input_method"]
        _, output = self.send_command(dumpsys_command)

        for line in output.decode().splitlines():
            if line.endswith("mScreenOn=true"):
                return True
            elif line.endswith("mScreenOn=false"):
                return False
        log.error("Can't know if screen is on, on device " + self.name)

    def install_apk(self, apk):
        # This command is sending message like:
        # 7480 KB/s (1329987 bytes in 0.173s)
        # on stderr, VERY WEIRD !!
        print("Installing APK on " + self.name)
        try:
            install_command = ["install", "-r", apk]
            result, out = self.send_command(install_command)
            str_out = str(out.decode())
            if "Success" not in str_out:
                quit(
                    "An error occurred during the installation (maybe the app "
                    "cannot be installed on this device ?): " + str_out, 1)
        except OSError as e:
            quit("An error occurred during the installation: {0}".format(e), 1)
        return True

    def get_apk_location(self, package):
        """ Return the path of the APK associated to package """
        pm_command = ["shell", "pm", "path", package]
        _, output = self.send_command(pm_command)
        if output:
            return output.decode().split(":")[1].splitlines()[0]
        else:
            log.error("Can't get APK location of " + package +
                      " on " + self.name)
            return ""

    def get_data_dir(self, package):
        """ Return the data directory of the package """
        cmd = ["shell", "pm", "dump", package]
        _, out = self.send_command(cmd)
        if not out:
            return None
        else:
            for line in out.decode().splitlines():
                if (line.find("dataDir") >= 0):
                    return line.split("=")[1]
            return None

    def start_activity(self, package, activity):
        log.debug("Starting Activity: " + package + "/" + activity)
        start_command = ["shell", "am", "start", "-n"
            , package + "/" + activity]
        self.send_command(start_command)

    def start_service(self, package, service):
        log.debug("Starting Service: " + package + "/" + service)
        start_command = ["shell", "am", "startservice"
            , package + "/" + service]
        self.send_command(start_command)

    def broadcast_intent(self, intent):
        log.debug("Broadcasting Intent: " + intent)
        broadcast_command = ["shell", "am", "broadcast", "-a", intent]
        self.send_command(broadcast_command)

    def kill_app(self, package):
        log.debug("Forcing stop of package: " + package)
        stop_command = ["shell", "am", "force-stop", package]
        self.send_command(stop_command)

    def twrp_flash(self):
        """ Flash the device using TWRP """
        # log.debug("Flashing device")
        # cmd = ["reboot", "recovery"]
        # self.send_command(cmd)
        # while not self.is_available("recovery"):
        #     time.sleep(10)
        #     if self.is_available("adb"):
        #         self.send_command(cmd)

        # if self.backup_changed():
        #     log.info("Backup files have been changed on the device")
        #     # Remove old backup
        #     cmd = ["shell", "rm", "-fr",
        #            "/sdcard/TWRP/BACKUPS/"
        #            "{0}/{1}.backup".format(self.name, self.image_name)]
        #     self.send_command(cmd)

        #     # Create the directory for the backup
        #     cmd = ["shell", "mkdir", "-p",
        #            "/data/media/0/TWRP/BACKUPS/"
        #            "{0}/{1}.backup".format(self.name, self.image_name)]
        #     self.send_command(cmd)

        #     # Push the clean backup on the device
        #     cmd = ["push", join(self.backup_dir,
        #                         "{0}.backup".format(self.image_name)),
        #            "/data/media/0/TWRP/BACKUPS/"
        #            "{0}/{1}.backup".format(self.name, self.image_name)]
        #     self.send_command(cmd)
        # else:
        #     log.info("Keeping backup files found on the device")

        # # Restore the backup
        # cmd = ["shell", "twrp", "restore",
        #        "{0}.backup".format(self.image_name)]
        # self.send_command(cmd)

        # # Reboot the device
        # cmd = ["reboot"]
        # self.send_command(cmd)
        # shutdown the genymotion vm by killing the process
        args = ['ps', 'x']
        p1 = subprocess.Popen(args, stdout=subprocess.PIPE)

        args = ['grep', 'Genymotion\.app/Contents/MacOS/.*player']
        p2 = subprocess.Popen(args, stdin=p1.stdout, stdout=subprocess.PIPE)

        args = ['awk', '{print $1}']
        p3 = subprocess.Popen(args, stdin=p2.stdout, stdout=subprocess.PIPE)

        args = ['xargs', 'kill']
        p4 = subprocess.Popen(args, stdin=p3.stdout, stdout=subprocess.PIPE)

        p1.stdout.close()
        p2.stdout.close()
        p3.stdout.close()
        p4.communicate()[0]

        # shut down the vm on virtual box
        args = ['vboxmanage', 'controlvm', 'STAS_Ex4', 'poweroff']
        subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]

        # wait until the vm and the processes are completely shut down
        time.sleep(2)

        # restore the virtual box snapshot for the android vm
        args = ['vboxmanage', 'snapshot', 'STAS_Ex4', 'restore', 'Reset']
        print(subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0])

        # leave time for restoring the snapshot
        time.sleep(3)

        # start genymotion vm
        args = ['open', '-a', '/Applications/Genymotion.app/Contents/MacOS/player.app', '--args', '--vm-name', '93c34e6b-b0df-4c5c-be32-b072220d943e']
        subprocess.Popen(args, stderr=subprocess.STDOUT,
                         stdout=subprocess.PIPE).communicate()[0]

        # wait until vm is completely booted
        time.sleep(30)

    def backup_changed(self):
        # Look for md5sum tool in the device
        cmd = ["shell", "ls", "/system/bin/busybox"]
        _, out = self.send_command(cmd)
        if "No such file or directory" not in str(out):
            md5sum_tool = "/system/bin/./busybox md5sum"
        else:
            cmd = ["shell", "ls", "/system/bin/md5sum"]
            _, out2 = self.send_command(cmd)
            if "No such file or directory" not in str(out2):
                md5sum_tool = "/system/bin/./md5sum"
            else:
                return True

        for f in os.listdir(join(self.backup_dir, "{0}.backup".
                format(self.image_name))):
            if not f.endswith("win"):
                continue
            cmd_r = ["shell", md5sum_tool,
                     "/sdcard/TWRP/BACKUPS/{0}/{1}.backup/{2}".
                     format(self.name, self.image_name, f)]
            cmd_l = ["cat", join(self.backup_dir,
                                 "{0}.backup/{1}.md5".
                                 format(self.image_name, f))]
            _, md5_remote = self.send_command(cmd_r)
            p = subprocess.Popen(cmd_l, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            md5_local, _ = p.communicate()
            md5_remote = str(md5_remote)
            md5_local = str(md5_local)
            if md5_remote and md5_local and md5_remote.find(" ") != -1 \
                    and md5_local.find(" ") != -1:
                md5_remote = md5_remote[:md5_remote.find(" ")]
                md5_local = md5_local[:md5_local.find(" ")]
                if md5_remote != md5_local:
                    return True
            else:
                return True
        return False
