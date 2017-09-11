import logging
import xml.etree.ElementTree as et
from manifest_parser.elements import *

log = logging.getLogger("mnfparser")


def manifest_from_apk(apk_filepath):
    """ Extracts the manifest from the file at apk_filepath and returns a
    Manifest object. """


class Manifest(object):
    """ Manifest of an Android application. """

    def __init__(self, manifest_path=None):
        if manifest_path:
            self.parse_file(manifest_path)
        else:
            self.reset()

    def reset(self):
        self.package_name = ""
        self.uses_sdk = {"min": "", "target": ""}
        self.activities = []
        self.services = []
        self.receivers = []
        self.metadata = []
        self.permissions = []

    def parse_file(self, manifest_path):
        """ Parse the given manifest file to collect information about the app.

        Args:
            manifest_path: path to the AndroidManifest.xml. It must be in text
            form, not the binary form shipped with the APKs. Most binary
            manifests can be reversed to their text form with *apktool*.
        """
        self.reset()

        tree = et.parse(manifest_path)
        root = tree.getroot()

        self.package_name = root.get("package")

        for child in root:
            if   child.tag == "uses-sdk":        self._parse_sdks(child)
            elif child.tag == "application":     self._parse_app(child)
            elif child.tag == "uses-permission": self._parse_perm(child)

    def _parse_sdks(self, sdks_node):
        """ Parse the "uses-sdk" node """
        self.uses_sdk["min"] = \
            Manifest._get_attr(sdks_node, "minSdkVersion") or ""
        self.uses_sdk["target"] = \
            Manifest._get_attr(sdks_node, "targetSdkVersion") or ""

    def _parse_app(self, app_node):
        """ Parse the application node. """
        for child in app_node:

            if child.tag == "activity":
                activity = self._parse_activity(child)
                self.activities.append(activity)

            elif child.tag == "service":
                service = self._parse_service(child)
                self.services.append(service)

            elif child.tag == "receiver":
                receiver = self._parse_receiver(child)
                self.receivers.append(receiver)

            elif child.tag == "meta-data":
                pair = {
                    "name": Manifest._get_attr(child, "name"),
                    "value": Manifest._get_attr(child, "value")
                }
                self.metadata.append(pair)

    def _parse_activity(self, activity_node):
        """ Parse an activity node and returns the corresponding Activity. """
        activity_name = Manifest._get_attr(activity_node, "name")
        if activity_name.startswith("."):
            activity_name = self.package_name + activity_name
        activity = Activity(activity_name)

        intent_filter = activity_node.find("intent-filter")
        if intent_filter is not None:
            for intent_child in intent_filter:
                intent = Intent(
                    Manifest._get_attr(intent_child, "name"),
                    Intent.TYPE.tag_value(intent_child.tag)
                )
                activity.intents.append(intent)

        return activity

    def _parse_service(self, service_node):
        service_name = Manifest._get_attr(service_node, "name")
        if service_name.startswith("."):
            service_name = self.package_name + service_name
        service = Service(service_name)

        return service

    def _parse_receiver(self, receiver_node):
        """ Parse an activity node and returns the corresponding Activity. """
        receiver_name = Manifest._get_attr(receiver_node, "name")
        if receiver_name.startswith("."):
            receiver_name = self.package_name + receiver_name
        receiver = Receiver(receiver_name)

        intent_filter = receiver_node.find("intent-filter")
        if intent_filter is not None:
            for intent_child in intent_filter:
                intent = Intent(
                    Manifest._get_attr(intent_child, "name"),
                    Intent.TYPE.tag_value(intent_child.tag)
                )
                receiver.intents.append(intent)

        return receiver

    def _parse_perm(self, perm_node):
        """ Parse the permission node. """
        perm = Permission(Manifest._get_attr(perm_node, "name"))
        self.permissions.append(perm)

    @staticmethod
    def _get_attr(node, attribute):
        """ Get attribute from ElementTree node, ignoring namespaces. """
        for attrib in node.attrib:
            if attrib.endswith("}" + attribute):
                return node.get(attrib)
        else:
            return None

    def get_main_activity(self):
        """ Return the first activity to match the criteria of the main one

        If no activity matches the criterias, return the first registered
        activity, or None if there is no registered activity.
        """
        for activity in self.activities:
            if activity.is_main_activity():
                return activity
        else:
            log.error("No main activity found!")

            if self.activities:
                first_activity = self.activities[0]
                log.warning( "Returning the first activity registered "
                             "({})".format(first_activity.name) )
                return first_activity
            else:
                log.warning("This application registers no activities!")
                return None

    def print_info(self):
        """ Print gathered data after parsing a manifest file. """
        print("Package: " + self.package_name)
        print("Minimal SDK: " + self.uses_sdk["min"])
        print("Target SDK: " + self.uses_sdk["target"])

        print("Activities:")
        for activity in self.activities:
            print("\t* " + activity.name)
            if activity.intents:
                print("\t  This activity filters the following intents:")
                for intent in activity.intents:
                    print("\t\t* " + intent.name)

        print("Services:")
        for service in self.services:
            print("\t* " + service.name)

        print("Intent receivers:")
        for receiver in self.receivers:
            print("\t* " + receiver.name + " waits for")
            for intent in receiver.intents:
                print("\t\t* " + intent.name)

        print("Meta-data:")
        for pair in self.metadata:
            print("\t* " + pair["name"] + " : " + pair["value"])

        print("Permissions:")
        for perm in self.permissions:
            print("\t* " + perm.name)
