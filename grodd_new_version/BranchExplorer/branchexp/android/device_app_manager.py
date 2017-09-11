import logging

log = logging.getLogger("branchexp")


class DeviceAppManager(object):
    """ Interface from managing apps of a Device. """

    def __init__(self, device):
        self.device = device

    def install_app(self, apk):
        """ Install this APK file on the device. """
        log.info("Installing APK on " + self.device.name)
        try:
            install_command = ["install", "-r", apk]
            self.device.send_command(install_command)
        except OSError as exc:
            quit("An error occured during the installation: " + str(exc), 1)
        return True

    def get_apk_location(self, package):
        """ Return the path of the APK associated to package on the device. """
        pm_command = ["shell", "pm", "path", package]
        _, output = self.device.send_command(pm_command)
        if output:
            return output.decode().split(":")[1].splitlines()[0]
        else:
            log.error( "Can't get APK location of " + package +
                       " on " + self.device.name )
            return ""

    def start_activity(self, package, activity):
        """ Start the activity from package. """
        log.debug("Starting Activity: " + package + "/" + activity)
        start_command = [ "shell", "am", "start", "-n"
                        , package + "/" + activity ]
        self.device.send_command(start_command)

    def start_service(self, package, service):
        """ Start the service from package. Note that it may need some rights
        to properly start. """
        log.debug("Starting Service: " + package + "/" + service)
        start_command = [ "shell", "am", "startservice"
                        , package + "/" + service ]
        self.device.send_command(start_command)

    def broadcast_intent(self, intent):
        """ Broadcast that intent on the device. """
        log.debug("Broadcasting Intent: " + intent)
        broadcast_command = ["shell", "am", "broadcast",  "-a", intent]
        self.device.send_command(broadcast_command, blocking = False)

    def kill_app(self, package):
        """ Terminate all components from this package. """
        log.debug("Forcing stop of package: {}".format(package))
        stop_command = ["shell", "am", "force-stop", package]
        self.device.send_command(stop_command)

    def uninstall_app(self, package):
        """
        :param package: Uninstall the app
        :return:
        """
        log.debug("Uninstalling the package: " + package)
        stop_command = ["uninstall", package]
        self.device.send_command(stop_command)
