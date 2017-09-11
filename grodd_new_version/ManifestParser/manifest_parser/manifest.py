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
        self.providers = []

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

            elif child.tag == "provider":
                provider = self._parse_provider(child)
                self.providers.append(provider)

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

    # CHANGED: added by me
    def _parse_provider(self, provider_node):
        provider_name = Manifest._get_attr(provider_node, "name")
        if provider_name.startswith("."):
            provider_name = self.package_name + provider_name

        return provider_name

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

        print("Providers:")
        for provider in self.providers:
            print("\t* " + provider.name)

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


    # ADDED BY ME
    def get_numerical_features(self):
        """ Store all numercial features fetched from the manifest file and return as a list """
        result = []

        # get sdk versions
        min_sdk = 0.0 if not self.uses_sdk["min"] else float(self.uses_sdk["min"])
        target_sdk = 0.0 if not self.uses_sdk["target"] else float(self.uses_sdk["target"])

        result.append(min_sdk)
        result.append(target_sdk)

        # get number of activities and intents
        activity_count, activity_intent_count = 0, 0

        for activity in self.activities:
            activity_count += 1
            if activity.intents:
                for intent in activity.intents:
                    activity_intent_count += 1

        result.append(activity_count)
        result.append(activity_intent_count)

        # get the number of services
        services_count = 0
        for service in self.services:
            services_count += 1
        result.append(services_count)

        # get the number of providers
        providers_count = 0
        for provider in self.providers:
            providers_count += 1
        result.append(providers_count)

        # get the number of intent receivers and intents
        receiver_count, receiver_intent_count = 0, 0
        for receiver in self.receivers:
            receiver_count += 1
            for intent in receiver.intents:
                receiver_intent_count += 1
        result.append(receiver_count)
        result.append(receiver_intent_count)

        # get specific permissions
        permissions_count, send_sms_perm, internet_perm, read_contacts_perm = 0, 0, 0, 0
        receive_sms_perm, read_sms_perm, write_sms_perm, delete_package_perm = 0, 0, 0, 0
        install_package_perm, write_settings_perm, location_perm, read_phone_state_perm = 0, 0, 0, 0
        read_call_logs_perm, process_call_perm, receive_mms_perm, call_phone_perm = 0, 0, 0, 0
        apn_perm, change_perm, record_audio_perm, clear_cache_perm = 0, 0, 0, 0
        boot_perm, get_accounts_perm, read_phone_numbers_perm, request_installing_packages_perm= 0, 0, 0, 0
        background_perm = 0

        for perm in self.permissions:
            permissions_count += 1.0
            if perm.name == "android.permission.SEND_SMS":
                send_sms_perm = 1.0
            if perm.name == "android.permission.INTERNET":
                internet_perm = 1.0
            elif perm.name == "android.permission.READ_CONTACTS":
                read_contacts_perm = 1.0
            elif perm.name == "android.permission.RECEIVE_SMS":
                receive_sms_perm = 1.00
            elif perm.name == "android.permission.READ_SMS":
                read_sms_perm = 1.0
            elif perm.name == "android.permission.WRITE_SMS":
                write_sms_perm = 1.0
            elif perm.name == "android.permission.DELETE_PACKAGES":
                delete_package_perm = 1.0
            elif perm.name == "android.permission.INSTALL_PACKAGES":
                install_package_perm = 1.0
            elif perm.name == "android.permission.WRITE_SETTINGS":
                write_settings_perm = 1.0
            elif perm.name == "android.permission.ACCESS_FINE_LOCATION" or \
                            perm.name == "android.permission.ACCESS_coarse_LOCATION":
                location_perm = 1.0
            elif perm.name == "android.permission.READ_PHONE_STATE":
                read_phone_state_perm = 1.0
            elif perm.name == "android.permission.READ_CALL_LOGS":
                read_call_logs_perm = 1.0
            elif perm.name == "android.permission.PROCESS_OUTGOING_CALLS":
                process_call_perm = 1.0
            elif perm.name == "android.permission.RECEIVE_MMS":
                receive_mms_perm = 1.0
            elif perm.name == "android.permission.CALL_PHONE":
                call_phone_perm = 1.0
            elif perm.name == "android.permission.WRITE_APN_SETTINGS" or \
                            perm.name == "android.permission.READ_APN_SETTINGS":
                apn_perm = 1.0
            elif perm.name == "android.permission.CHANGE_WIFI_STATE" or \
                            perm.name == "android.permission.CHANGE_CONFIGURATION" or \
                            perm.name == "android.permission.CHANGE_NETWORK_STATE":
                change_perm = 1.0
            elif perm.name == "android.permission.RECORD_AUDIO":
                record_audio_perm = 1.0
            elif perm.name == "android.permission.CLEAR_APP_CACHE":
                clear_cache_perm = 1.0
            elif perm.name == "android.permission.RECEIVE_BOOT_COMPLETED":
                boot_perm = 1.0
            elif perm.name == "android.permission.GET_ACCOUNTS":
                get_accounts_perm = 1.0
            elif perm.name == "android.permission.READ_PHONE_NUMBERS":
                read_phone_numbers_perm = 1.0
            elif perm.name == "android.permission.REQUEST_INSTALL_PACKAGES":
                request_installing_packages_perm = 1.0
            elif perm.name == "android.permission.RUN_IN_BACKGROUND":
                background_perm = 1.0

        result.append(send_sms_perm)
        result.append(internet_perm)
        result.append(read_contacts_perm)
        result.append(read_sms_perm)
        result.append(receive_sms_perm)
        result.append(write_sms_perm)
        result.append(delete_package_perm)
        result.append(install_package_perm)
        result.append(write_settings_perm)
        result.append(location_perm)
        result.append(read_phone_state_perm)
        result.append(read_call_logs_perm)
        result.append(process_call_perm)
        result.append(receive_mms_perm)
        result.append(call_phone_perm)
        result.append(apn_perm)
        result.append(change_perm)
        result.append(record_audio_perm)
        result.append(clear_cache_perm)
        result.append(boot_perm)
        result.append(get_accounts_perm)
        result.append(read_phone_numbers_perm)
        result.append(request_installing_packages_perm)
        result.append(background_perm)
        result.append(permissions_count)

        return result
