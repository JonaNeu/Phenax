#!/usr/bin/python
import os
import sys

def listLogs():
    tmp = os.popen("adb shell \"ls /data/data/org.blareids.logger/logs\"").readlines()
    files = []
    for f in tmp:
	files.append(f.replace('\r\n', ''))
    return files

def pullFiles(lesFiles, folder):
    for f in lesFiles:
	os.system("adb pull /data/data/org.blareids.logger/logs/"+f +" "+folder)

# MAIN
if len(sys.argv) != 2:
    print "Usage : "+ sys.argv[0] + " <folder_name>"
else:
    files = listLogs()
    print str(len(files)) + " log(s) to retrieve"
    pullFiles(files, sys.argv[1])
