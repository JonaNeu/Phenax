echo "Pushing script and busybox"
adb push log.sh /data/data/org.blareids.logger
adb push busybox /system/bin
adb shell "chmod 555 /system/bin/busybox"
adb shell "mkdir /data/data/org.blareids.logger/logs"
echo -n "Setting system Time\n "
#adb shell date -s `date "+%Y%m%d.%H%M%S"`
adb shell date -s `date "+%Y%m%d"`.84003
echo "Setting system tags to 0"
adb shell "setinfo /system/bin/surfaceflinger 0"
adb shell "setinfo /system/bin/servicemanager 0"
