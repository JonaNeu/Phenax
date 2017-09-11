#!/usr/bin/env python

import os
import sys
import subprocess
from androguard.core.bytecodes.apk import APK as APK

if (len(sys.argv) < 5):
    print("main.py <apk_dir> <result dir> <device_serial_number>"
          "<device_codename>")
    exit(0)

apk_dir = os.path.abspath(sys.argv[1])
res_dir = os.path.abspath(sys.argv[2])
dev = sys.argv[3]
code = sys.argv[4]

if not (os.path.isdir(apk_dir)):
    print("{0} does not exist".format(apk_dir))
    exit(0)

if not (os.path.isdir(res_dir)):
    os.mkdir(res_dir)

done_before = list()
log_path = os.path.join(res_dir, "analysed.txt")
if os.path.isfile(log_path):
    log = open(log_path, "r")
    for line in log.read().splitlines():
        done_before.append(os.path.basename(line))
    log.close()
log = open(log_path, "a")
f_output = open(os.path.join(res_dir, "rawoutput.txt"), "a")

print "Ready to process {0}".format(apk_dir)
cur_dir = os.curdir
# os.chdir(os.path.join(os.path.dirname(__file__),
#                       "BranchExplorer"))
for root, dlist, flist in os.walk(apk_dir):
    for f in flist:
        if (f in done_before):
            print "{0} has already been analysed. Skipped".format(f)
            continue
        apk = os.path.join(root, f)
        try:
            a = APK(apk)
        except:
            continue
        print "Sample: {}".format(os.path.basename(apk))
        output = os.path.join(res_dir, "{0}.res".format(apk.split("/")[-1]))
        # cmd = ["sh", "/Users/rado/blare/twrpbackup/flash.sh", dev, code]
        # subprocess.call(cmd)
        cmd = ["python3",
               "-m",
               "branchexp.main",
               # "--device",
               # dev,
               # "--device-code",
               # code,
               # "--run-type",
               # "grodd",
               # "--max-runs",
               # "2",
               "--output-dir",
               output,
               apk
               ]
        p = subprocess.Popen(cmd, stdout=f_output, stderr=f_output)
        p.wait()
        cmd = ["adb", "-s", dev, "shell", "pm", "uninstall", a.get_package()]
        p = subprocess.Popen(cmd, stdout=f_output, stderr=f_output)
        p.wait()
        log.write("{0}\n".format(apk))
        log.flush()
os.chdir(cur_dir)
log.close()
