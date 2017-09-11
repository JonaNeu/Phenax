import device


def init_devices():
    config_device = {}

    # Liste des devices Kharon
    config_device["3034D685CCDD00EC", "product_name"] = "crespo"
    config_device["3034D685CCDD00EC", "name"] = "Kharon 0a"

    config_device["3735710E119600EC", "product_name"] = "crespo"
    config_device["3735710E119600EC", "name"] = "Kharon 0b"

    config_device["3033A362952100EC", "product_name"] = "crespo"
    config_device["3033A362952100EC", "name"] = "Kharon 0c"

    config_device["04a8ed0c4388943c", "product_name"] = "crespo"
    config_device["04a8ed0c4388943c", "name"] = "Kharon 0d"

    config_device["0e51880bf1646216", "product_name"] = "hammerhead"
    config_device["0e51880bf1646216", "name"] = "Kharon0"

    config_device["0a9dd409f1646022", "product_name"] = "hammerhead"
    config_device["0a9dd409f1646022", "name"] = "Kharon1"

    config_device["0e51853e0d5cbb7e", "product_name"] = "hammerhead"
    config_device["0e51853e0d5cbb7e", "name"] = "Kharon2"

    config_device["0aa6a5db0d5cd6e8", "product_name"] = "hammerhead"
    config_device["0aa6a5db0d5cd6e8", "name"] = "Kharon3"

    config_device["0640a4980acd72e1", "product_name"] = "hammerhead"
    config_device["0640a4980acd72e1", "name"] = "Kharon4"

    config_device["04a8ed0c4388943c", "product_name"] = "hammerhead"
    config_device["04a8ed0c4388943c", "name"] = "Kharon5"

    config_device["013ea5bb224db199", "product_name"] = "bullhead"
    config_device["013ea5bb224db199", "name"] = "5X LIFO 2"

    config_device["013ea5c922959b97", "product_name"] = "bullhead"
    config_device["013ea5c922959b97", "name"] = "5X LIFO 3"

    config_device["0140295722adbb93", "product_name"] = "bullhead"
    config_device["0140295722adbb93", "name"] = "5X LIFO 4"

    config_device["013fd7b63f9fc075", "product_name"] = "bullhead"
    config_device["013fd7b63f9fc075", "name"] = "5X LIFO 5"


    # Config propre au product name
    config_device["crespo", "backup_dir"] = "/tmp"
    config_device["crespo", "rom_stock"] = "https://gforge.inria.fr/frs/download.php/file/36015/crespo_4.0.2.stock.zip"
    config_device["crespo", "rom_androblare"] = "https://gforge.inria.fr/frs/download.php/file/36016/crespo_4.0.2.androblare.zip"

    config_device["hammerhead", "backup_dir"] = "/tmp"
    config_device["hammerhead", "rom_stock"] = "https://gforge.inria.fr/frs/download.php/file/36039/hammerhead_4.4.2.stock.zip"
    config_device["hammerhead", "rom_androblare"] = "https://gforge.inria.fr/frs/download.php/file/36037/hammerhead_4.4.2.androblare.zip"

    config_device["bullhead", "backup_dir"] = "/tmp"
    config_device["bullhead", "rom_stock"] = "https://www.dropbox.com/s/x17p4im49tic88r/bullhead_6.0.1.stock.zip?dl=0"
    config_device["bullhead", "rom_androblare"] = ""

    return config_device
