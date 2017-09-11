1) Install TWRP on Android devices (flash recovery)
[https://twrp.me/Devices/]:
================================================
(If you already have TWRP installed skip this step, to check `adb reboot
recovery`)

* Downlaod TWRP image for this specific device (3.x seems incompatible
with Nexus 5), then
* `adb reboot bootloader`
* Then `sudo ./fastboot oem device-info`, if it shows like
"(bootloader)    Device unlocked: true" you can continue,
   else do `fastboot flashing unlock` or `fastboot oem unlock` depending
on the device
* Flash TWRP to the device: `fastboot flash recovery twrp.img`, where
twrp.img is the downloaded TWRP image, change the name if needed
* `fastboot reboot` while holding the volume down button (or the
corresponding
   combination/button for your device) pressed to reboot to the revocery
mode.
   (If you are on Nexus 5 just use volume buttons to navigate to
"Recovery mode" and press the power button)
* if a custom recovery shows up the installation is successful, else try
again with another TWRP version.
* Now you can reboot the phone to the normal mode if needed

2) Restore a backup from command line:
=========================

Use case: install a backup from gforge with blare preinstalled
(https://gforge.inria.fr/frs/?group_id=6121)
Available backups on gforge:
* hammerhead.backup.tar.gz: Android 4.4.2 for Nexus 5, with Blare
preinstalled
* crespo.backup.tar.gz: Android 4.0.4 for Nexus S, with Blare preinstalled

Download the corresponding backup archive file
Decompress it
You need just the folder containing the .win files, we will call this
folder: <twrp_backup_name>, eg: crespo.backup and hammerhead.backup
So cd to its parent folder

$ adb devices # to get the <device_serial_number>
$ adb -s <device_serial_number> reboot recovery
$ adb -s <device_serial_number> shell rm -rf
/sdcard/TWRP/BACKUPS/<device_serial_number>/<twrp_backup_name>
$ adb -s <device_serial_number> shell mkdir -p
/sdcard/TWRP/BACKUPS/<device_serial_number>/<twrp_backup_name>/
$ adb -s <device_serial_number> push <backup_name>/
/sdcard/TWRP/BACKUPS/<device_serial_number>/<twrp_backup_name>/
$ adb -s <device_serial_number> shell twrp restore <twrp_backup_name>
$ adb -s <device_serial_number> reboot
You will boot to the new system

