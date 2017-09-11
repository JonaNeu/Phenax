__author__ = 'acemond'

import logging
from os.path import join
import random
import re
import subprocess
import time
import xml.etree.ElementTree as et

log = logging.getLogger("groddrunner")

from uiautomator import Device

from acfg_tools.builder.utils import SOOT_SIG

from branchexp.runners.base_runner import Runner
from branchexp.utils.utils import quit


class GroddRunner(Runner):
    """ This Runner tries to explore interface in a more intelligent way. Sadly
    that's all I can say because I don't understand much about what it does. """

    TIME_BETWEEN_INTERACTIONS = .25

    # How many times should we skip no UI Elt found before pressing back button?
    SKIP_COUNT = 5
    # How many times should we skip no UI Elt at launch? (loading screens)
    INIT_MAX_SKIP = 10
    # How many times should we try back before trying XML elts again?
    MAX_BACK_EVENT = 1

    MAX_CYCLE = 1000

    # Timeout in seconds
    TIMEOUT = 60

    # Take the content-desc variable from XML elements into account?
    CHECK_CONTENT_DESC = True
    # Take the content-desc variable from XML elements into account?
    CHECK_BOUNDS = True

    # UI EVENTS
    DEV_INPUT_EVENT = 1

    # temp files
    DEVICES_FILE = "devices.tmp"
    XML_FILE = "xml.tmp"
    FOCUS_FILE = "focus.tmp"

    def __init__(self, infos):
        super().__init__(infos)

        self.temp_device_file = join(self.output_dir, GroddRunner.DEVICES_FILE)
        self.temp_xml_file = join(self.output_dir, GroddRunner.XML_FILE)
        self.temp_focus_file = join(self.output_dir, GroddRunner.FOCUS_FILE)

        self.triggered_elts = []
        self.encountered_elts = []
        self.crashing_elts = []
        self.dead_end_elts = []

        self.main_activity = ""
        self.entry_activity = ""

    def run(self):
        self.prepare_run()
        self.start_logcat()

        self.handle_entry_points()
        self.start_looping()

        self.stop_logcat()
        self.clean_after_run()

    def handle_entry_points(self):
        """ Load main and entry activity according to manifest infos and given
        entry point. """
        self._find_main_activity()
        self._find_entry_activity()

    def _find_main_activity(self):
        """ Set self.main_activity to an appropriate activity or exit if it
        simply can't. """
        main_activity = self.manifest.get_main_activity()
        if main_activity is not None:
            self.main_activity = main_activity.name
        else:
            quit("No activity available.")

    def _find_entry_activity(self):
        """ Find an appropriate activity to use as an entry point, considering
        given entry point, and set self.entry_activity accordingly. """
        self.entry_activity = self.main_activity

        if self.entry_point is not None:
            entry_point_sig = SOOT_SIG.match(self.entry_point).groupdict()
            entry_point_class = entry_point_sig["class"]
            log.info("Given entry point class " + entry_point_class)

            for activity in self.manifest.activities:
                if entry_point_class == activity.name:
                    log.info("Found entry activity " + entry_point_class)
                    self.entry_activity = entry_point_class
                    break
            else:
                log.info("No activity named " + entry_point_class)
                self._process_special_entry_point(entry_point_class)

    def _process_special_entry_point(self, entry_point_class):
        """ Process non-activity entry point. It can start services or broadcast
        intents to receivers. """
        log.warning( "Processing special entry points requires, most of the "
                     "time, exported services in the manifest, "
                     "or a rooted device." )

        for service in self.manifest.services:
            if entry_point_class == service.name:
                log.info("Found entry service " + entry_point_class)
                log.info("Starting this service")
                self.device.app_manager.start_service( self.package_name
                                                     , entry_point_class )
                return

        for receiver in self.manifest.receivers:
            if entry_point_class == receiver.name:
                log.info("Found entry broadcast receiver " + entry_point_class)
                if receiver.intents:
                    log.info("Sending an appropriate Intent")
                    intent = receiver.intents[0]
                    self.device.app_manager.broadcast_intent(intent.name)
                else:
                    log.warning("No Intent for receiver " + entry_point_class)
                return

    def start_looping(self):
        """ Launch the execution of the application """
        self.device.app_manager.start_activity( self.package_name
                                              , self.entry_activity )
        log.info('Starting loop on UI elements.')

        ui_elements = []
        init_skip = 0
        d = Device(self.device.name)
        while not len(ui_elements):
            d.dump(self.temp_xml_file)
            self.find_ui_element(self.temp_xml_file, ui_elements)
            time.sleep(1)
            init_skip += 1
            if init_skip > GroddRunner.INIT_MAX_SKIP:
                log.error("No UI Element came out, aborting tests...")
                return

        self.process_elements(ui_elements)

    def process_elements(self, ui_elements):
        """ Cycle over elements in ui_elements. """
        skipped = 0
        cycle_count = -1
        back_event_sent = 0

        encountered_states = []
        last_triggered = None
        start_time = time.time()
        d = Device(self.device.name)
        while True:
            cycle_count += 1
            if cycle_count > GroddRunner.MAX_CYCLE:
                log.info("Too many interactions (probable loop), stopping.")
                break
            if (time.time() - start_time) > GroddRunner.TIMEOUT:
                log.info("Test is taking too long, stopping.")
                break

            should_continue = self.check_app_status(last_triggered)
            if not should_continue:
                break

            ui_elements = []
            d.dump(self.temp_xml_file)
            self.find_ui_element(self.temp_xml_file, ui_elements, triggered=[])
            state = list(ui_elements)
            ui_elements = []
            self.find_ui_element(self.temp_xml_file, ui_elements)

            if not len(ui_elements):
                log.info("Didn't find any relevant interaction!")
                if self.all_list0_elements_in_list1(self.encountered_elts,
                                                    self.triggered_elts):
                    log.info( "Successfully triggered all elements "
                              "encountered" )
                    break
                elif skipped < GroddRunner.SKIP_COUNT:
                    log.debug("Skip")
                    skipped += 1
                    time.sleep(GroddRunner.TIME_BETWEEN_INTERACTIONS)
                    continue
                elif back_event_sent < GroddRunner.MAX_BACK_EVENT:
                    log.debug( "Added last element to dead ends: "
                               + str(last_triggered) )
                    self.dead_end_elts.append(last_triggered)
                    self.device.ui.go_back()
                    log.debug('BACK sent!')
                    back_event_sent += 1
                    last_triggered = 'back'
                    skipped = 0
                    time.sleep(GroddRunner.TIME_BETWEEN_INTERACTIONS)
                    continue
                else:
                    log.debug("Only dead-ends here.")

                    back_event_sent = 0
                    self.find_ui_element(self.temp_xml_file, ui_elements,
                                         triggered=[])
                    if not len(ui_elements):
                        last_triggered = None
                        self.device.kill_app(self.package_name)
                        continue

            if state:
                if not self.state_in_list(state, encountered_states):
                    all_elts_triggered = True
                    for elt in state:
                        if not self.xml_element_in_list(elt,
                                                        self.triggered_elts):
                            all_elts_triggered = False
                    if all_elts_triggered:
                        encountered_states.append(state)
                else:
                    log.debug( "Just looped, "
                               "there was a useless UI element" )
                    if last_triggered is not None:
                        if last_triggered != 'back':
                            if not self.xml_element_in_list(
                                    last_triggered, self.dead_end_elts):
                                self.dead_end_elts.append(last_triggered)

            log.info( "Encountered Elements:  "
                      + str(len(self.encountered_elts)) )
            log.info( "Triggered Elements:    "
                      + str(len(self.triggered_elts)) )
            log.info( "Dead-end Elements:     "
                      + str(len(self.dead_end_elts)) )
            log.info( "Possible Elements:     "
                      + str(len(ui_elements)) )

            ui_element = GroddRunner.select_random_but_first(ui_elements)
            log.debug("Triggering: " + ui_element.get("text"))
            self.trigger_element(ui_element)
            last_triggered = ui_element

            time.sleep(GroddRunner.TIME_BETWEEN_INTERACTIONS)

    def state_in_list(self, new_state, state_list):
        for state in state_list:
            if self.all_list0_elements_in_list1(state, new_state):
                return True
        return False

    def check_app_status(self, last_triggered):
        current_package = get_running_app_package(self.device.name)[0]
        if current_package != self.package_name:
            log.debug('App Stopped!')
            log.debug('Last Action: ' + str(last_triggered))
            if last_triggered is not None:
                if last_triggered == "back":
                    log.warning( "Cannot access remaining XML elements. "
                                 "Quitting..." )
                    log.info( "Managed to Trigger: "
                              + str(len(self.triggered_elts))
                              + " elements out of "
                              + str(len(self.encountered_elts)) )
                    return False
                else:
                    log.debug( "Previous XML element caused application "
                               "to quit. Elements removed from tests." )
                    self.crashing_elts.append(last_triggered)
            else:
                log.warning( "Failed to identify crashing element. "
                             "Quitting..." )
                return False

            log.debug('Relaunching tests...')
            # Never sure enough
            if current_package == self.package_name:
                self.device.kill_app(self.package_name)
            self.device.app_manager.start_activity( self.package_name
                                                  , self.entry_activity )
        return True

    def find_ui_element(self, xml_file, ui_elements,
                        triggered=None, dead=None):
        triggered_elts = triggered
        dead_end_elts = dead
        if triggered is None:
            triggered_elts = self.triggered_elts
        if dead is None:
            dead_end_elts = self.dead_end_elts
        tree = et.parse(xml_file)
        root = tree.getroot()

        self.search_in_tree(root, ui_elements, triggered_elts, 'clickable')
        if not ui_elements:
            self.search_in_tree(root, ui_elements, dead_end_elts, 'clickable')

    def search_in_tree(self, node, ui_elements, excluded_elts,
                       prop='clickable'):
        for child in node:
            if child.get("enabled") == "true":
                if child.get(prop) == "true" and (
                   not self.xml_element_in_list(child, self.crashing_elts)):
                    if not self.xml_element_in_list(child,
                                                    self.encountered_elts):
                        self.encountered_elts.append(child)
                    if not self.xml_element_in_list(child, excluded_elts):
                        ui_elements.append(child)
                self.search_in_tree(child, ui_elements, excluded_elts,
                                    prop)

    def find_scrollable_element(self, xml_file, scrollable_elements):
        tree = et.parse(xml_file)
        root = tree.getroot()
        self.search_in_tree(root, scrollable_elements, [], 'scrollable')

    @staticmethod
    def select_random_but_first(elts_list):
        # Cette méthode prend un élément au hasard dans la liste SAUF le
        # premier élément. S'il n'y a qu'un élément, il est choisi.
        # Pourquoi ce comportement ?!
        if len(elts_list) > 1:
            random_index = random.randrange(1, len(elts_list))
            return elts_list[random_index]
        elif len(elts_list) == 1:
            return elts_list[0]

    def trigger_element(self, xml_element):
        bounds_string = xml_element.get("bounds")
        if bounds_string:
            bounds = self.read_bounds(bounds_string)
            if bounds is not None:
                x_coord = (bounds[0][0] + bounds[1][0]) / 2.0
                y_coord = (bounds[0][1] + bounds[1][1]) / 2.0
                self.device.ui.touch(x_coord, y_coord)

        if not self.xml_element_in_list(xml_element, self.triggered_elts):
            self.triggered_elts.append(xml_element)

    @classmethod
    def all_list0_elements_in_list1(cls, xml_list0, xml_list1):
        for xml_elt in xml_list0:
            if not cls.xml_element_in_list(xml_elt, xml_list1):
                return False
        return True

    @classmethod
    def xml_element_in_list(cls, xml_elt, xml_list):
        for list_elt in xml_list:
            if cls.same_xml_elements(xml_elt, list_elt):
                return True
        return False

    @classmethod
    def same_xml_elements(cls, elt0, elt1):

        def has_same_attribute_value(elt0, elt1, attribute):
            return elt0.get(attribute) == elt1.get(attribute)

        for attribute in ("text", "resource-id", "class", "package"):
            if not has_same_attribute_value(elt0, elt1, attribute):
                return False

        if ( GroddRunner.CHECK_BOUNDS
             and not has_same_attribute_value(elt0, elt1, "bounds") ):
            return False

        if ( GroddRunner.CHECK_CONTENT_DESC
             and not has_same_attribute_value(elt0, elt1, "content-desc") ):
            return False

        return True

    @classmethod
    def read_bounds(cls, bounds_string):
        inst = re.compile(r"""
        \[(\d+),(\d+)\]                  # x0, y0
        \[(\d+),(\d+)\]                  # x1, y1
        """, re.VERBOSE)

        match = inst.match(bounds_string)

        if match is not None:
            x0_coord = int(match.group(1))
            y0_coord = int(match.group(2))
            x1_coord = int(match.group(3))
            y1_coord = int(match.group(4))
            return [[x0_coord, y0_coord], [x1_coord, y1_coord]]
        else:
            return [[0, 0], [0, 0]]


def get_running_app_package(device_name):
    get_windows_process = subprocess.Popen(
        [ "adb", "-s", device_name,
          "shell", "dumpsys", "window", "windows" ],
        stdin = subprocess.PIPE, stdout = subprocess.PIPE
    )

    get_windows_process.wait()
    output = get_windows_process.stdout.read().decode()

    package = re.compile(r"""
    \s*mFocusedApp=AppWindowToken
    \{
        [0-9a-zA-Z]+\s*token=Token
        \{
            [0-9a-zA-Z]+\s*ActivityRecord
            \{
                [0-9a-zA-Z]+\s*[0-9a-zA-Z]+\s
                ( [0-9a-zA-Z\.]+ )  # Package Name
                /
                ( [0-9a-zA-Z\.]+ )  # Activity Name
                \s*[0-9a-zA-Z]+
            \}
        \}
    \}
    """, re.VERBOSE)

    for line in output.splitlines():
        if "mFocusedApp" in line:
            break
    else:
        line = ""

    match = package.match(line)
    if match is not None:
        package_name = match.group(1)
        activity_name = match.group(2)
        return [package_name, activity_name]
    else:
        return [None, None]
