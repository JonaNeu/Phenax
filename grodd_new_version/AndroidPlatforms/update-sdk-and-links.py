#!/bin/python3

import argparse
import subprocess

print("This script will update your sdk with all the versions of the SDK build tools.")

parser = argparse.ArgumentParser(description='Get SDK location.')
parser.add_argument('--sdk', metavar='S', type=str, required=True, help='the path of the sdk')
args = parser.parse_args()
print("Updating SDK in " + args.sdk)
sdk=args.sdk

version = "android-10 android-13 android-16 android-19 android-3 android-6 android-9 android-11 android-14 android-17 android-20 android-4 android-7 android-12 android-15 android-18 android-21 android-5 android-8"

s = version.split(" ")
print(s)
for v in s:
    print("===============================================================================")
    subprocess.call("echo y | " + sdk + "/tools/android update sdk -u -a -t " + v + " && ln -s " + sdk + "/platforms/" + v, shell=True)
    print("===============================================================================")


print("All done !")
