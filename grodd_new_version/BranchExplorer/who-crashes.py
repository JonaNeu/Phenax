#!/usr/bin/env python3
""" Determines what applications crashes just after start in a dataset. """

import os
import shutil
import subprocess
import time

from manifest_parser.manifest import Manifest


DATASET = "/home/shgck/boulot/StageM2/Malwares/Dataset Malcon/PROCESS_ME"
WORKING_DIR = "/tmp/who-crashes"

APKTOOL = "/home/shgck/dev/Android/Apktool/apktool"

DEVICE = "0640a4980acd72e1"
DEVICE_CODE = "hammerhead"


def main():
    shutil.rmtree(WORKING_DIR, ignore_errors = True)
    os.makedirs(WORKING_DIR, exist_ok = True)

    for f in os.listdir(DATASET):
        if os.path.splitext(f)[1] == ".apk":
            apk = os.path.join(DATASET, f)
            process_apk(apk)

    # shutil.rmtree(WORKING_DIR, ignore_errors = True)


def process_apk(apk):
    apk_name = os.path.basename(apk)
    print("Processing APK " + apk_name)

    apk_dir = os.path.join(WORKING_DIR, os.path.basename(apk_name) + ".dir")
    os.makedirs(apk_dir, exist_ok = True)

    extract_resources(apk, apk_dir)
    manifest = Manifest(os.path.join(apk_dir, "AndroidManifest.xml"))
    package_name = manifest.package_name
    print("Package name: " + package_name)

    has_crashed = check_if_app_crashes(apk, package_name)
    result = "RESULT FOR " + apk_name + " : has crashed? = " + str(has_crashed)
    print(result)
    with open("who-crashes.log", "a") as log_file:
        log_file.write(result + "\n")


def extract_resources(apk, output_dir):
    print("Extracting resources")
    shutil.rmtree(output_dir, ignore_errors = True)
    extract_command = [APKTOOL, "d", apk, "-s", "-o", output_dir]
    subprocess.call(extract_command)


def check_if_app_crashes(apk, package_name):
    install_apk(apk)
    has_crashed = start_monkey_and_check_crashes(package_name)
    # has_crashed = not check_app_is_alive(package_name)
    uninstall_apk(package_name)
    return has_crashed


def install_apk(apk):
    print("Installing")
    install_command = ["adb", "-s", DEVICE, "install", "-r", apk]
    subprocess.call(install_command)


def uninstall_apk(package_name):
    print("Uninstalling")
    uninstall_command = [ "adb", "-s", DEVICE
                        , "shell", "pm", "uninstall", package_name ]
    subprocess.call(uninstall_command)


def start_monkey_and_check_crashes(package_name):
    print("Starting Monkey")
    monkey_command = [ "adb", "-s", DEVICE
                     , "shell", "monkey"
                     , "-p", package_name
                     , "-v", "500" ]
    
    raw_output = subprocess.check_output(monkey_command)
    time.sleep(1)
    
    monitored_text = "CRASH: " + package_name
    output = raw_output.decode()
    if monitored_text in output:
        return True
    else:
        return False


# def check_app_is_alive(package_name):
#     print("Checking if " + package_name + " is alive")
#     check_command = [ "adb", "-s", DEVICE
#                     , "shell", "ps" ]
#     raw_output = subprocess.check_output(check_command)
#     output = raw_output.decode()

#     for line in output.splitlines():
#         print("> " + line)
#         if package_name in line:
#             return True
#     return False


if __name__ == '__main__':
    main()
