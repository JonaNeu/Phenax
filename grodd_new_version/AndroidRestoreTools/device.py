# Global library
import logging, sys, time, os.path
from os.path import join as join
from os.path import dirname as dirname

# Local library
import sdk

log = logging.getLogger("AndroidRestoreTools")


class Device(object):
    """ Interface for an Android device. """

    def __init__(self, name, product_name, uuid, rom_stock, rom_androblare, backup_dir):
        self.name = name
        self.product_name = product_name
        self.uuid = uuid
        self.rom_stock = rom_stock
        self.rom_androblare = rom_androblare
        self.backup_dir = backup_dir
        self.choice = 0

    def send_command( self, command, tool = "adb", blocking = True
                    , stdin = None, stdout = None ):
        """ Send a command to this device (by default through ADB). """
        tool_command = [tool, "-s", self.uuid] + command
        return sdk.send_command(
            tool_command, blocking = blocking,
            stdin = stdin, stdout = stdout
        )
    def set_choice(self, choice):
        self.choice = choice

    def exec_choice(self):
        if(self.choice == 1):
            self.fastboot_flash()
        elif(self.choice == 2):
            self.twrp_flash()
        else:
            return


    # def send_key_event(self, event_code):
    #     """ Send an event of integer value 'event_code' to the device. """
    #     event_command = ["shell", "input", "keyevent", str(event_code)]
    #     return self.send_command(event_command)
    #
    # def wait_until_ready(self, mode = "adb"):
    #     """ Wait until device shows up in ADB and is fully booted. """
    #     sys.stdout.flush()
    #
    #     log.info("Waiting for " + self.name + " to be available")
    #     while not self.is_available(mode = mode):
    #         time.sleep(2)
    #
    #     log.info("Waiting for " + self.name + " to be fully booted")
    #     while not self.is_booted():
    #         time.sleep(2)
    #
    #     log.info("Device " + self.name + " is ready.")
    #

    # Fct permettant de résoudre les problèmes de connexions
    def is_connected(self):
        test_command = ["shell", "exit"]
        result, output = self.send_command(test_command)
        if(result != 0):
            print("[ERREUR] Connexion perdue ... Redémarrage de ADB")
            time.sleep(5)
            sdk.send_command(["adb", "usb"])
            time.sleep(5)
            result, output = self.send_command(test_command)

            if(result != 0):
                print("[ERREUR] Impossible de rétablir la connexion")
                return False
            else:
                print("[INFO] Connexion rétablie")
                return True
        else:
            return True


    def is_available(self, mode = "adb"):
        """ Check if device appears in ADB or fastboot devices """
        check_command = list()
        if (mode == "recovery"):
            check_command.append("adb")
        else:
            check_command.append(mode)
        check_command.append("devices")
        result, output = sdk.send_command(check_command)
        for line in output.decode().splitlines():
            if line.startswith(self.uuid):
                if (mode == "adb" and line.endswith("device")):
                    # exception pour Nexus S
                    getprop_command = ["shell", "getprop", "sys.boot_completed"]
                    _, output = self.send_command(getprop_command)
                    for line in output.decode().splitlines():
                        if line.strip("\r\n") == "1":
                            return True
                    return False
                elif((mode == "fastboot" and line.endswith("fastboot")) or (mode == "recovery" and line.endswith("recovery"))):
                    return True
                elif (mode == "recovery" and line.endswith("device")):
                    # exception pour Nexus S
                    getprop_command = ["shell", "getprop", "sys.boot_completed"]
                    _, output = self.send_command(getprop_command)
                    for line in output.decode().splitlines():
                        if line.strip("\r\n") == "":
                            return True
                    return False

        return False

    # def is_booted(self):
    #     """ Check if an available device has completed its boot. """
    #     getprop_command = ["shell", "getprop", "sys.boot_completed"]
    #     _, output = self.send_command(getprop_command)
    #     for line in output.decode().splitlines():
    #         if line.strip("\r\n") == "1":
    #             return True
    #     return False
    #
    # def remount_system_rw(self):
    #     """ Remount /system partition of this device in read&write mode. """
    #     log.debug("Remount /system in RW mode")
    #     remount_command = ["shell", "mount", "-o", "rw,remount", "/system"]
    #     self.send_command(remount_command)
    #
    # def wake_device(self):
    #     """ Send some key events to wakeup the screen if it isn't on. """
    #     if not self.is_screen_on():
    #         self.send_key_event(POWER_BUTTON_CODE)
    #         time.sleep(2)
    #     self.send_key_event(MENU_BUTTON_CODE)
    #
    # def is_screen_on(self):
    #     """ Check if the device screen is on (= shows something). """
    #     dumpsys_command = ["shell", "dumpsys", "input_method"]
    #     _, output = self.send_command(dumpsys_command)
    #
    #     for line in output.decode().splitlines():
    #         if line.endswith("mScreenOn=true"):
    #             return True
    #         elif line.endswith("mScreenOn=false"):
    #             return False
    #     log.error("Can't know if screen is on, on device " + self.name)
    #
    # def install_apk(self, apk):
    #     log.info("Installing APK on " + self.name)
    #     try:
    #         install_command = ["install", "-r", apk]
    #         result, out = self.send_command(install_command)
    #         str_out = str(out.decode())
    #         if "Success" not in str_out:
    #             quit("An error occurred during the installation (maybe the app cannot be installed on this device ?): " + str_out, 1)
    #     except OSError as e:
    #         quit("An error occurred during the installation: " + e, 1)
    #     return True
    #
    # def get_apk_location(self, package):
    #     """ Return the path of the APK associated to package """
    #     pm_command = ["shell", "pm", "path", package]
    #     _, output = self.send_command(pm_command)
    #     if output:
    #         return output.decode().split(":")[1].splitlines()[0]
    #     else:
    #         log.error( "Can't get APK location of " + package +
    #                    " on " + self.name )
    #         return ""
    #
    # def get_data_dir(self, package):
    #     """ Return the data directory of the package """
    #     cmd = ["shell", "pm", "dump", package]
    #     _, out = self.send_command(cmd)
    #     if not out:
    #         return None
    #     else:
    #         for line in out.decode().splitlines():
    #             if (line.find("dataDir") >= 0):
    #                 return line.split("=")[1]
    #         return None
    #
    # def start_activity(self, package, activity):
    #     log.debug("Starting Activity: " + package + "/" + activity)
    #     start_command = [ "shell", "am", "start", "-n"
    #                     , package + "/" + activity ]
    #     self.send_command(start_command)
    #
    # def start_service(self, package, service):
    #     log.debug("Starting Service: " + package + "/" + service)
    #     start_command = [ "shell", "am", "startservice"
    #                     , package + "/" + service ]
    #     self.send_command(start_command)
    #
    # def broadcast_intent(self, intent):
    #     log.debug("Broadcasting Intent: " + intent)
    #     broadcast_command = ["shell", "am", "broadcast",  "-a", intent]
    #     self.send_command(broadcast_command)
    #
    # def kill_app(self, package):
    #     log.debug("Forcing stop of package: " + package)
    #     stop_command = ["shell", "am", "force-stop", package]
    #     self.send_command(stop_command)

    def twrp_flash(self):
        """ Flash the device using TWRP """
        print("Lancement de la procédure de flashage avec la ROM Androblare")
        cmd = ["reboot", "recovery"]
        print("Redémmarage de l'appareil en mode Recovery")
        while not self.is_available("recovery"):
            result, output = self.send_command(cmd)
            time.sleep(10)
            if(not self.is_connected()):
                return

            # if not self.is_available("adb"):
            #     self.send_command(cmd)

        print("Appareil en mode Recovery")


        if(self.rom_androblare == ""):
            print("[ERREUR] Aucun lien de téléchargement androblare pour l'appareil")
            return

        if(not os.path.isfile(join(self.backup_dir, self.product_name + ".backup" + ".zip"))):
            download_command = ["wget", "-q", self.rom_androblare, "-O", join(self.backup_dir, self.product_name + ".backup" +".zip")]
            print("[INFO] Téléchargement de l'image correspondante")
            result, output = sdk.send_command(download_command)
            if(result != 0):
                print("[ERREUR] Impossible de télécharger le zip")
                return

        if(not os.path.isdir(join(self.backup_dir, self.product_name + ".backup"))):
            unzip_command = ["unzip", "-q", join(self.backup_dir,"{0}.backup".format(self.product_name)), "-d", join(self.backup_dir, "{0}.backup".format(self.product_name))]
            print("[INFO] Décompression du ZIP")
            result, output = sdk.send_command(unzip_command)
            if(result != 0):
                print("[ERREUR] Impossible de décompresser le ZIP")
                return

        print("Supression de l'ancien backup")

        # Remove old backup
        # TODO Do this only if the content of the backup has changed
        cmd = ["shell", "rm", "-fr", "/sdcard/TWRP/BACKUPS/" + "{0}/{1}.backup".format(self.uuid, self.product_name)]
        self.send_command(cmd)

        # Create the directory for the backup
        cmd = ["shell", "mkdir", "-p", "/sdcard/TWRP/BACKUPS/" + "{0}/{1}.backup".format(self.uuid, self.product_name)]
        self.send_command(cmd)


        # Push the clean backup on the device
        cmd = ["push", join(self.backup_dir, "{0}.backup".format(self.product_name)), "/sdcard/TWRP/BACKUPS/" + "{0}/{1}.backup".format(self.uuid, self.product_name)]
        self.send_command(cmd)

        # Restore the backup
        cmd = ["shell", "twrp", "restore",
               "{0}.backup".format(self.product_name)]
        self.send_command(cmd)

        # Reboot the device
        cmd = ["reboot"]
        self.send_command(cmd)

    def fastboot_flash(self):
        """ Flash the device using Fastboot """
        print("Lancement de la procédure de flashage avec la ROM Stock")
        # print("Lancement de la procédure de flashage avec la ROM Androblare")
        cmd = ["reboot", "bootloader"]
        while not self.is_available("fastboot"):
            result, output = self.send_command(cmd)
            time.sleep(10)
            if not self.is_available("fastboot"):
                self.send_command(cmd)

        if(self.rom_stock == ""):
            print("[ERREUR] Aucun lien de téléchargement de ROM Stock pour l'appareil")
            return

        if(not os.path.isfile(join(self.backup_dir, self.product_name + ".stock" + ".zip"))):
            download_command = ["wget", self.rom_stock, "-O", join(self.backup_dir, self.product_name + ".stock" +".zip")]
            print("[INFO] Téléchargement de l'image correspondante")
            result, output = sdk.send_command(download_command)
            if(result != 0):
                print("[ERREUR] Impossible de télécharger le zip")
                return

        # Restore the backup
        cmd = ["-w", "update", join(self.backup_dir, "{0}.stock.zip".format(self.product_name))]
        result, output = self.send_command(cmd, "fastboot")

        # if(result == 1):
        #     print("[INFO] Version du bootloader incorrecte")
        #     print("[INFO] Voulez mettre à jour le bootloader [DANGEREUX] ?")
        #     value = input("Taper 'Entrer' pour continuer ou 'q' pour quitter")
        #     if(value == 'q'):
        #         return
        #     else:
        #


        # if(not os.path.isdir(join(self.backup_dir, self.product_name + ".backup"))):
        #     unzip_command = ["unzip", "-q", join(self.backup_dir,"{0}.backup".format(self.product_name)), "-d", join(self.backup_dir, "{0}.backup".format(self.product_name))]
        #     print("[INFO] Décompression du ZIP")
        #     result, output = sdk.send_command(unzip_command)
        #     if(result != 0):
        #         print("[ERREUR] Impossible de décompresser le ZIP")
        #         return
