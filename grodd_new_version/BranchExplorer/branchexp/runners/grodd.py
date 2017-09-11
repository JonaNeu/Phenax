__author__ = 'acemond'

import hashlib
import logging
from os.path import join
import random
import re
import subprocess
import time
from collections import defaultdict
import xml.etree.ElementTree as et
from uiautomator import Device
from acfg_tools.builder.utils import SOOT_SIG
from branchexp.runners.base_runner import Runner
from branchexp.utils.utils import quit

log = logging.getLogger("branchexp")

# CHANGED: added by me

import signal, time
from contextlib import contextmanager

class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

TIME_LIMIT = 300 # run each app for 5 mins = 300 sec


class GroddRunner(Runner):
    """ This Runner tries to explore interface in a more intelligent way. Sadly
    that's all I can say because I don't understand much about what it does. """

    TIME_BETWEEN_INTERACTIONS = .2 #.25

    # How many times should we skip no UI Elt found before pressing back button?
    SKIP_COUNT = 5
    # How many times should we skip no UI Elt at launch? (loading screens)
    INIT_MAX_SKIP = 10
    # How many times should we try back before trying XML elts again?
    MAX_BACK_EVENT = 1

    MAX_CYCLE = 1000

    # Timeout in seconds
    TIMEOUT = 300

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

    def __init__(self, info):
        super().__init__(info)

        self.device_ui = Device(self.device.name)
        self.temp_device_file = join(self.output_dir, GroddRunner.DEVICES_FILE)
        self.temp_xml_file = join(self.output_dir, GroddRunner.XML_FILE)
        self.temp_tree = None
        self.temp_tree_root = None
        self.temp_focus_file = join(self.output_dir, GroddRunner.FOCUS_FILE)

        self.triggered_elts = []
        self.encountered_elts = []
        self.crashing_elts = []
        self.dead_end_elts = []

        self.main_activity = ""
        self.entry_activity = ""

        self.automaton = {} # Etats connus de l'automate (clé: hash, valeur: State)
        self.initialStateHash = None # Hashé du premier état rencontré

        # Transitions à trigger
        # Cette liste pourra être complétée au fur et à mesure de l'algorithme de parours
        self.to_trigger = [GroddRunner.State.BACK, GroddRunner.State.CLICK]

        # Surtout utile au debug, à la visualisation de l'automate
        self.nbOfStates = 0 # Nombre d'états connus
        self.stateMap = {} # Pour la numérotation des états

    def run(self):
        self.prepare_run()
        self.start_logcat()

        self.handle_entry_points()

        # CHANGED: added the paranthsis around the run_apk call
        try:
            with time_limit(TIME_LIMIT):
                self.start_looping()
        except TimeoutException:
            print("App execution takes longer than 5 min, shutting it down")
        #self.start_looping()

        self.stop_logcat()
        self.clean_after_run()

    def handle_entry_points(self):
        """ Load main and entry activity according to manifest info and given
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
            log.debug("Given entry point class " + entry_point_class)

            for activity in self.manifest.activities:
                if entry_point_class == activity.name:
                    log.debug("Found entry activity " + entry_point_class)
                    self.entry_activity = entry_point_class
                    break
            else:
                log.debug("No activity named " + entry_point_class)
                self._process_special_entry_point(entry_point_class)

    def _process_special_entry_point(self, entry_point_class):
        """ Process non-activity entry point. It can start services or broadcast
        intents to receivers. """
        log.warning( "Processing special entry points requires, most of the "
                     "time, exported services in the manifest, "
                     "or a rooted device." )

        for service in self.manifest.services:
            if entry_point_class == service.name:
                print("Found entry service {}, Starting it..."
                      .format(entry_point_class))
                self.device.app_manager.start_service( self.package_name
                                                     , entry_point_class )
                return

        for receiver in self.manifest.receivers:
            if entry_point_class == receiver.name:
                print("Found entry broadcast receiver " + entry_point_class)
                if receiver.intents:
                    print("Sending an appropriate Intent")
                    intent = receiver.intents[0]
                    self.device.app_manager.broadcast_intent(intent.name)
                else:
                    log.warning("No Intent for receiver " + entry_point_class)
                return

    def start_looping(self):
        """ Launch the execution of the application """
        self.device.app_manager.start_activity( self.package_name
                                              , self.entry_activity )
        print('Start looping on UI elements.')

        time.sleep(1)

        ui_elements = []
        init_skip = 0
        # d = Device(self.device.name)
        # TODO La condition de boucle sera changée pour l'adapter à l'automate

        # TODO: ADD counter to restict the number of elements looped over

        while not len(ui_elements):
            self.dump()
            self.find_ui_element(ui_elements)
            time.sleep(0.2)
            init_skip += 1
            if init_skip > GroddRunner.INIT_MAX_SKIP:
                log.error("No UI Element came out, aborting tests...")
                return

        self.process_elements_automaton(ui_elements)

    def dump(self):
        self.device_ui.dump(self.temp_xml_file)
        self.temp_tree = et.parse(self.temp_xml_file)
        self.temp_tree_root = self.temp_tree.getroot()

    def process_elements(self, ui_elements):
        """ Cycle over elements in ui_elements. """
        skipped = 0
        cycle_count = -1
        back_event_sent = 0

        encountered_states = []
        last_triggered = None
        start_time = time.time()
        d = self.device_ui
        while True:
            cycle_count += 1
            if cycle_count > GroddRunner.MAX_CYCLE:
                print("Too many interactions (probable loop), stopping.")
                break
            if (time.time() - start_time) > GroddRunner.TIMEOUT:
                print("Test is taking too long, stopping.")
                break

            should_continue = self.check_app_status(last_triggered)
            if not should_continue:
                break

            ui_elements = []
            self.dump()
            self.find_ui_element(ui_elements, triggered=[])
            state = list(ui_elements)
            ui_elements = []
            self.find_ui_element(ui_elements)

            if not len(ui_elements):
                print("Didn't find any relevant interaction!")
                if self.all_list0_elements_in_list1(self.encountered_elts,
                                                    self.triggered_elts):
                    print( "Successfully triggered all elements "
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
                    self.device_ui.press.back()
                    log.debug('BACK sent!')
                    back_event_sent += 1
                    last_triggered = 'back'
                    skipped = 0
                    time.sleep(GroddRunner.TIME_BETWEEN_INTERACTIONS)
                    continue
                else:
                    log.debug("Only dead-ends here.")

                    back_event_sent = 0
                    self.find_ui_element(ui_elements,
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

            log.debug("Encountered Elements:  "
                      + str(len(self.encountered_elts)) )
            log.debug("Triggered Elements:    "
                      + str(len(self.triggered_elts)) )
            log.debug("Dead-end Elements:     "
                      + str(len(self.dead_end_elts)) )
            log.debug("Possible Elements:     "
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
        current_package = self.get_running_package()
        if current_package != self.package_name:
            log.debug('App Stopped! {} != {}'.format(current_package,
                                                     self.package_name))
            log.debug('Last Action: ' + str(last_triggered))
            if last_triggered is not None:
                if last_triggered == "back":
                    log.warning( "Cannot access remaining XML elements. "
                                 "Quitting..." )
                    print( "Managed to Trigger: "
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

    def check_app_status_automaton(self):
        current_package = self.get_running_package()
        if current_package != self.package_name:
            log.debug('Left application.')
            log.debug('Relaunching app...')
            # Never sure enough
            if current_package == self.package_name:
                self.device.kill_app(self.package_name)
            self.device.app_manager.start_activity( self.package_name
                                                  , self.entry_activity )
            return True
        return False

    def find_ui_element(self, ui_elements,
                        triggered=None, dead=None):
        triggered_elts = triggered
        dead_end_elts = dead
        if triggered is None:
            triggered_elts = self.triggered_elts
        if dead is None:
            dead_end_elts = self.dead_end_elts
        root = self.temp_tree_root

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
                # self.device.ui.touch(x_coord, y_coord)
                self.device_ui.click(x_coord, y_coord)

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

    @staticmethod
    def read_bounds(bounds_string):
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

    @staticmethod
    def get_bounds( xml_element ):
        bounds_string = xml_element.get("bounds")
        if bounds_string:
            bounds = GroddRunner.read_bounds(bounds_string)
            return bounds
        return None

    def get_running_package(self):
        return self.device_ui.info.get(u'currentPackageName', None)

    class Transition:
        # Transition entre 2 états
        def __init__( self, bounds, action, state = None ):
            self.bounds = bounds
            self.action = action
            self.state = state

    class State:
        # Etat de l'automate de l'application
        # Un état peut être identifié "de manière unique" par le hashé de l'arbre XML.
        # Les transitions sont les actions possibles depuis cet état
        # 
        # NB: Un état n'est pas forcément une activité, il est défini de manière plus précise

        # TODO A compléter
        BACK = -1
        CLICK = 0
        LONG_CLICK = 1
        SCROLL = 2
        SWIPE = 3
        
        actions = ['clickable','long-clickable']

        def __init__( self, root, theId = None ):
            if not theId:
                h = hashTree( root )
                self.id = h.digest()
            else:
                self.id = theId
            self.transitions = []
            # Note importante : le premier élément qui peut être triggered a la taille de l'écran tout entier
            self.constructTransitions(root)

            self.transitions.append( GroddRunner.Transition(None, GroddRunner.State.BACK) )
            # TODO ajouter les actions par défaut (back, ...)

        def constructTransitions( self, node ):
            bounds = None # On ne calcule les bounds que si c'est nécessaire
            if node.get("enabled") == "true":
                for (name, value) in node.items():
                    try:
                        action = GroddRunner.State.actions.index(name)
                        if not bounds:
                            bounds = GroddRunner.get_bounds( node )
                            if not bounds:
                                break
                        self.transitions.append( GroddRunner.Transition(bounds, action) )
                    except ValueError:
                        pass

            for child in node:
                self.constructTransitions( child )

        # La liste ignored est à compléter (si on ne veut pas inclure certains items dans le hash)
        @staticmethod
        def hashTree( root, ignored = ['checked', 'text'] ):
            h = hashlib.sha256()
            GroddRunner.State.hashNode( root, h, ignored )
            return h.hexdigest()

        def hashNode( node, currentHash, ignored ):
            # Fonction récursive qui renvoie un hash correspondant à l'arbre XML
            currentHash.update( repr(len(node)).encode('utf-8') )

            for (name, value) in node.items():
                if not name in ignored:
                    currentHash.update(name.encode('utf-8'))
                    currentHash.update( repr(value).encode('utf-8') )

            for child in node:
                GroddRunner.State.hashNode( child, currentHash, ignored )

    def process_elements_automaton(self, ui_elements):
        # Essaie de parcourir l'application en reconstruisant l'automate
        # des états/activités possibles
        start_time = time.time()
        d = Device(self.device.name)
        cycle_count = 0

        fullyBrowsed = False
        targetActions = []
        lastTransition = None
        currentState = None
        while not fullyBrowsed:
            self.printAutomaton()

            # Nb de cycles et timeout
            cycle_count += 1
            if cycle_count > GroddRunner.MAX_CYCLE:
                log.info("Too many interactions (probable loop), stopping.")
                break
            if (time.time() - start_time) > GroddRunner.TIMEOUT:
                log.info("Test is taking too long, stopping.")
                break

            # Si l'application a fermé sur la dernière action, la transition sera juste comptée
            # comme une boucle vers l'état initial
            relaunched = self.check_app_status_automaton()

            # Récupération de l'arbre XML et de l'état courant
            self.dump()
            currentStateHash = GroddRunner.State.hashTree( self.temp_tree_root )
            if not self.initialStateHash:
                self.initialStateHash = currentStateHash
            if relaunched and currentStateHash != self.initialStateHash:
                log.info("Invalid initial state !")
                break
            if not currentStateHash in self.automaton:
                # L'état n'a jamais été rencontré
                currentState = GroddRunner.State( self.temp_tree_root, currentStateHash )
                self.automaton[currentStateHash] = currentState
                if lastTransition:
                    lastTransition.state = currentState

                self.nbOfStates += 1
                self.stateMap[currentStateHash] = self.nbOfStates
            else:
                # L'état est connu
                currentState = self.automaton[currentStateHash]
                if lastTransition:
                    if not lastTransition.state:
                        lastTransition.state = currentState
                    else:
                        if lastTransition.state != currentState:
                            log.info("The automaton is incorrect, and the algorithm cannot finish. Stopping.")
                            # Apparemment l'automate est incorrect, un état a été mal détecté
                            break

            if not targetActions:
                # On cherche une transition dont l'état d'arrivée est inconnu
                (relaunch, targetActions) = self.findNextTransition( currentState )
                if relaunch:
                    log.info("Need a reboot to browse the app")
                    self.device.kill_app(self.package_name)
                    self.device.app_manager.start_activity( self.package_name
                                                          , self.entry_activity )
                    self.dump()
                    currentStateHash = GroddRunner.State.hashTree( self.temp_tree_root )
                    if currentStateHash != self.initialStateHash:
                        log.info("The initial state is different from the first time. Aborting...")
                        break

                    currentState = self.automaton[currentStateHash]
                    (relaunch, targetActions) = self.findNextTransition( currentState )
                    if relaunch or not targetActions:
                        log.info("Unexpected error... aborting")
                        break

                if not targetActions:
                    # Fin de l'algorithme
                    fullyBrowsed = True
                    log.info("Successfully browsed all the automaton.")
                    break

            self.triggerTransition( targetActions[0] )
            lastTransition = targetActions[0]
            targetActions.pop(0)
        if fullyBrowsed:
            log.info("Fin normale de l'algorithme.")
        else:
            log.info("L'algorithme n'a pas fini normalement...")

    def findNextTransition( self, currentState ):
        # Effectue un parcours en largeur de l'automate en recherche d'une transition inconnue
        states = [currentState.id] # Etats parcourus
        toBrowse = [] # Suites de transitions utilisées dans le parcours
        shuffledTransitions = GroddRunner.shuffleTransi(currentState.transitions)
        for transi in shuffledTransitions:
            if transi.action in self.to_trigger:
                if not transi.state:
                    return (False, [transi])
                toBrowse.append( [transi] )

        while True:
            if not toBrowse:
                # On ne peut plus parcourir d'état
                for s in self.automaton.values():
                    if not s.id in states:
                        # Cet état est inaccessible
                        for t in s.transitions:
                            if transi.action in self.to_trigger:
                                if not t.state:
                                    # Cette transition nécessite de relancer l'application
                                    return (True, None)
                return (False, None)

            tmp = [] # Prochain toBrowse
            for path in toBrowse:
                s = path[-1].state
                shuffledTransitions = GroddRunner.shuffleTransi(s.transitions)
                for transi in shuffledTransitions:
                    if transi.action in self.to_trigger:
                        if not transi.state:
                            return (False, path + [transi])
                        if not transi.state.id in states:
                            tmp.append( path+[transi] )
                            states.append( transi.state.id )
            toBrowse = tmp

    @staticmethod
    def shuffleTransi( transi ):
        res = list(transi)
        random.shuffle(res)
        for t in res:
            if t.action == GroddRunner.State.BACK:
                res.remove(t)
                res.append(t)
                return res
        return res

    def triggerTransition( self, transition ):
        if transition.action == GroddRunner.State.BACK:
            self.device_ui.press.back()
        elif transition.action == GroddRunner.State.CLICK:
            x_coord = (transition.bounds[0][0] + transition.bounds[1][0]) / 2.0
            y_coord = (transition.bounds[0][1] + transition.bounds[1][1]) / 2.0
            self.device_ui.click(x_coord, y_coord)
        elif transition.action == GroddRunner.State.LONG_CLICK:
            x_coord = (transition.bounds[0][0] + transition.bounds[1][0]) / 2.0
            y_coord = (transition.bounds[0][1] + transition.bounds[1][1]) / 2.0
            self.device_ui.long_click(x_coord, y_coord)

    # Debug printing statement
    def printAutomaton( self ):
        print("   --------------- AUTOMATE ---------------   ")
        for i, state in self.automaton.items():
            print("Etat " + ( "%4s" % str(self.stateMap[i]) ) + ":")
            for transition in state.transitions:
                if transition.action in self.to_trigger:
                    msg = " -- "
                    if transition.bounds:
                        msg += "%12s" % (str(transition.bounds[0][0]) + "," + str(transition.bounds[1][0]))
                        msg += " - "
                        msg += "%-12s" % (str(transition.bounds[0][1]) + "," + str(transition.bounds[1][1]) )
                    else:
                        msg += "%12s" % "X,X"
                        msg += " - "
                        msg += "%-12s" % "X,X"
                    msg += ":  A" + ( "%4s" % str(transition.action) ) + "  ->  "
                    if transition.state:
                        msg += str(self.stateMap[transition.state.id])
                    else:
                        msg += "???"
                    print(msg)
        print("")

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
                ( [0-9a-zA-Z\._-]+ )  # Package Name
                /
                ( [0-9a-zA-Z\._-]+ )  # Activity Name
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

    #log.info("Package line: {}".format(line))
    match = package.match(line)
    if match is not None:
        package_name = match.group(1)
        activity_name = match.group(2)
        return [package_name, activity_name]
    else:
        return [None, None]
