#!/usr/bin/env python3
""" Android Restore Tools to flash with a Stock or Blare ROM """

import argparse, logging, os, sys
import sdk
import config
import device as dev

DESCRIPTION = "Manager for flashing different devices easily, with Stock ROM or Androblare ROM"

def main():
    print("".ljust(64,"*"))
    print("Lancement de l'outils de flashage automatisé")
    print("".ljust(64,"*"))
    if(not sdk.command_is_available("adb")):
        return
    if(not sdk.command_is_available("fastboot")):
        return
    config_device = config.init_devices()
    devices = []
    list_devices, info_device = sdk.detectDevice()
    for uuid in list_devices:
        if (uuid, "product_name") in config_device:
            product_name = info_device[uuid, "product_name"]
            if(product_name == config_device[uuid, "product_name"]):
                devices.append(dev.Device(config_device[uuid, "name"], product_name, uuid, config_device[product_name, "rom_stock"], config_device[product_name, "rom_androblare"], config_device[product_name, "backup_dir"]))
        else:
            print("[ERREUR] Appareil " + uuid + " non reconnu, veuillez rentrer la configuration dans le fichier config.py")
    for device in devices:
        sdk.what_do_you_do(device)
    for device in devices:
        device.exec_choice()



def setup_args():
    parser = argparse.ArgumentParser(description = DESCRIPTION)

    parser.add_argument("--apk_path", type = str, dest = "apk_path",
        help = "path to the APK")
    parser.add_argument("--device", type = str, dest = "device",
        help = "name of the device to use")
    parser.add_argument("--device-code", type = str, dest = "device_code",
        help = "device code to use")
    parser.add_argument("--run-type", type = str, dest = "run_type",
        help = "type of automatic run to do")
    parser.add_argument("--max-runs", type = str, dest = "max_runs",
        help = "maximum limit on number of runs")
    parser.add_argument("--output-dir", type = str, dest = "output_dir",
        help = "output directory of run_# subdirs")

    return parser.parse_args()



if __name__ == "__main__":
    main()
