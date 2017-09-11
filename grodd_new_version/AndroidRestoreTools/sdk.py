import logging, os, re, subprocess

log = logging.getLogger("AndroidRestoreTools")

def command_is_available(command):
    value = True
    try:
        process = subprocess.Popen(command, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            value = False
            print("[ERREUR] Commande", command, "introuvable.")
        else:
            value = False
            print("[ERREUR] Impossible de lancer la commande", command)
    return value

def send_command(command, blocking = True, stdin = None, stdout = None):
    """ Send a command in a subprocess.

    If blocking is True, return the return value and binary output.
    """
    if stdin is None:
        stdin = subprocess.PIPE
    if stdout is None:
        stdout = subprocess.PIPE

    log.debug("Sending command: " + " ".join(command))
    process = subprocess.Popen(command, stdin = stdin, stdout = stdout)

    result = None
    output = ""
    if blocking:
        result = process.wait()
        output = process.stdout.read()
    return result, output

def detectDevice():
    detect_command = ["adb", "devices"]
    list_devices = []
    info_device = {}
    _, output = send_command(detect_command)
    for line in output.decode().splitlines():
        if (line.endswith("device") or line.endswith("recovery")):
            device = line.split("\t")[0]
            mode = line.split("\t")[1]
            info_device[device, "mode"] = mode
            list_devices.append(device)
    detect_command = ["fastboot", "devices"]
    _, output = send_command(detect_command)
    for line in output.decode().splitlines():
        if (line.endswith("fastboot")):
            device = line.split("\t")[0]
            mode = line.split("\t")[1]
            info_device[device, "mode"] = mode
            list_devices.append(device)
    print("Liste des appareils détectés :")
    print("UUID".ljust(16) + "\t" + "Product Name".ljust(12) + "\t" + "Mode".ljust(12))
    print("".ljust(64,"-"))
    for device in list_devices:
        _, output = send_command(["adb", "-s", device, "shell", "getprop", "ro.product.device"])
        info_device[device, "product_name"] = output.decode().splitlines()[0]
        print(device + "\t" + info_device[device, "product_name"].ljust(12) + "\t" + info_device[device, "mode"].ljust(12))
    return list_devices, info_device

def what_do_you_do(device):
    """ Fct who ask to user what type of flash (stock or androblare) """
    print("Que souhaitez-vous faire avec l'appareil suivant : " + device.name)
    print("".ljust(32,"-"))
    print("| Device name".ljust(16), device.name)
    print("| Product device".ljust(16), device.product_name)
    print("| UUID".ljust(16), device.uuid)
    print("".ljust(32,"-"))
    print("0.\t Ne rien faire")
    print("1.\t Flasher avec la ROM Stock")
    print("2.\t Flasher avec la ROM Androblare")
    choice = -1
    while(choice < 0 or choice > 2):
        choice = int(input("Merci d'indiquer le numéro de votre choix et de valider par entrer : "))
        if(choice < 0 or choice > 2):
            print("Merci d'indiquer un numéro de choix correct")
    if(choice == 1):
        print("ROM Stock sélectionnée pour " + device.name)
        device.set_choice(choice)
    elif(choice == 2):
        print("ROM Androblare sélectionnée :" + device.name)
        device.set_choice(choice)
    else:
        return


def flash(device, partition, image):
    """ Flash an image to a partition using fastboot. """
    if not partition in ("system", "userdata", "boot"):
        raise Exception(partition + " is not a valid partition")
    if not os.path.isfile(image):
        raise Exception(image + " is not a file")

    log.debug("Flashing partition " + partition + " with image " + image)
    flash_command = ["flash", partition, image]
    result, _ = device.send_command(flash_command, tool = "fastboot")
    if result != 0:
        raise Exception(
            "Error when flashing device {}.\n{}".format(device.name, result)
        )


def get_package_name(apk):
    """ Get the package name from this APK, using aapt. """
    aapt_command = ["aapt", "dump", "badging", apk]
    try:
        aapt_output = subprocess.check_output(aapt_command).decode()
    except (OSError, subprocess.CalledProcessError) as exception:
        log.error("Failed to use aapt: " + str(exception))
        return None

    for line in aapt_output.splitlines():
        if line.startswith("package:"):
            return re.search(r"name='([\.\w]+)'", line).group(1)

    log.error("Unexpected output from aapt.")
    return None
