from uiautomator import Device
import random
import logging
import branchexp.runners.state as z
from branchexp.runners.base_runner import Runner
from branchexp.utils.utils import quit
import time
from threading import Thread
import branchexp.runners.chrono_method as chronom


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



log = logging.getLogger("branchexp")
z.log = log.info
z.debug = log.debug

class GroddRunner2(Runner):
    """ This is the second version of GroddRunner.
    It uses the backend module "state" to explore an Android app,
    by dynamically and smartly constructing and discovering an automaton of
    Android activities """

    MAX_PRIO = 2000 # It is the max prio of the transition itself until it is ignored
    PRIO_CHANGE_STATE = 300 # Cost of changing state (see findNextTransition)
    PRIO_NOT_VISIBLE = 50   # Cost of making an element visible if not already

    WAITING_TIME = 0 # Waiting time between interactions

    @chronom.chronomethod
    def __init__(self, info = None):
        super().__init__(info)
        self.device_ui = Device(self.device.name)

        # Properly loads the state module
        if info.context != "":
            log.info("Restoring context from " + info.context)
            z.Context.fromFile(info.context).apply(self.device_ui)
        else:
            z.init(self.device_ui)

        # Queue of transitions to trigger
        if info.trigger != "":
            log.info("Loading transitions from " + info.trigger)
            self.loadTransitions( info.trigger )
            self.forceTrigger = True
        else:
            self.toTrigger = []
            self.forceTrigger = False
        self.triggered = []
        self.fullyBrowsed = False

        self.stop = False

        self.currentState = None
        self.initialState = None
        self.previousState = None

    @chronom.chronomethod
    def findNextTransition(self):
        """ Find a path to an unknown transition in the existing automaton
        Returns the path, and if the app needs to reboot to trigger this path """
        states = [self.currentState.index] # Encountered states

        # From this state
        toBrowse = []
        potentialTransi = []
        for t in self.currentState.transitions:
            if self.MAX_PRIO == -1 or t.prio <= self.MAX_PRIO:
                if t.end is not None:
                    s = z.State.states[t.end].index
                    if s not in states:
                        toBrowse.append( (self.PRIO_CHANGE_STATE, [t]) )
                        states.append(s)
                else:
                    p = t.prio
                    if not z.isVisible(t.lindex):
                        p += self.PRIO_NOT_VISIBLE
                    potentialTransi.append( (p, [t]) )

        while True:
            # Only keep the transitions at the lowest prio
            minPrio = -1
            for prio,path in potentialTransi:
                if minPrio == -1 or minPrio > prio:
                    minPrio = prio
            tmp = []
            for prio,path in potentialTransi:
                if prio == minPrio:
                    tmp.append( (prio,path) )
            potentialTransi = tmp
            
            # prio in toBrowse should be all the same
            if potentialTransi:
                if toBrowse:
                    minPrio2,a = toBrowse[0]
                else:
                    minPrio2 = None
                if minPrio2 is None or minPrio < minPrio2:
                    # Then there won't be a better transition with a lower prio
                    # Choose a random transition
                    i = random.randrange(0,len(potentialTransi))
                    return (False, potentialTransi[i][1])

            if not toBrowse:
                # We cannot browse anymore from the current transitions
                for s in z.State.remainingStates:
                    if not s in states:
                        # Unaccessible state
                        for t in z.State.states[s].transitions:
                            if self.MAX_PRIO == -1 or t.prio <= self.MAX_PRIO:
                                if t.end is None:
                                    log.debug( "Target : " + t.toDebugString() )
                                    return (True,None)
                return (False,None)

            tmp = [] # Next toBrowse
            for prio,path in toBrowse:
                s = path[-1].end # By construction, s is not None
                for t in z.State.states[s].transitions:
                    if self.MAX_PRIO == -1 or t.prio <= self.MAX_PRIO:
                        if t.end is not None:
                            s2 = z.State.states[t.end].index
                            if s2 not in states:
                                tmp.append( (prio + self.PRIO_CHANGE_STATE, path + [t]) )
                                states.append(s2)
                        else:
                            p = prio + t.prio
                            if not z.isVisible(t.lindex):
                                p += self.PRIO_NOT_VISIBLE
                            potentialTransi.append( (p, path + [t]) )

            toBrowse = tmp

    @chronom.chronomethod
    def trigger(self):
        """ Trigger the next queued transition, and adapt the automaton consequently """
        # If no transition in queue, find one
        if not self.toTrigger:
            if self.stop:
                return True

            if self.forceTrigger:
                # It has finished triggering the transitions in the trigger file
                self.forceTrigger = False
                log.debug("Finished imposed transitions. Continuing...")

            (relaunch, tt) = self.findNextTransition()
            self.toTrigger = tt
            if relaunch:
                log.info("Need a reboot to browse the app")
                self.device.kill_app(self.package_name)
                self.device.app_manager.start_activity( self.package_name
                                                      , self.entry_activity )
                self.previousState = None
                self.currentState = z.State.insert( z.State() )
                if self.currentState.compare( self.initialState ) is z.Comparison.DIFFERENT:
                    log.info("The initial state is different from the first time. Go on...")
                    #TODO Do something ?
                    return True

                (relaunch, targetActions) = self.findNextTransition()
                self.toTrigger = tt
                if relaunch or not targetActions:
                    log.info("Unexpected error... aborting")
                    return False

            if not self.toTrigger:
                # Fin de l'algorithme
                self.fullyBrowsed = True
                log.info("Successfully browsed all the automaton.")
                return True
            elif len(self.toTrigger) > 1:
                target = self.toTrigger[-1]
                #print("Target : " + target.toDebugString() )

        if self.stop:
            return True

        tmpT = self.toTrigger[0]
        if not self.forceTrigger:
            t = self.currentState.getTransition(tmpT)
            if t is None:
                log.debug("Strange transition...")
                return False
        else:
            t = tmpT

        # Trigger transition
        log.debug( "Triggering " + t.toDebugString() )
        self.currentState.setVisible(t.lindex)
        t.trigger()
        self.triggered.append(t)
        self.toTrigger.pop(0)

        # Relaunch if needed
        relaunched = self.checkRelaunch()

        # Change state
        self.previousState = self.currentState
        time.sleep( self.WAITING_TIME )
        self.currentState = z.State.insert( z.State() )

        if self.stop:
            return True

        if t.end is None:
            t.end = self.currentState.index
        else:
            s = z.State.states[t.end]
            comp = self.currentState.compare(s)
            if comp == z.Comparison.SIMILAR:
                #self.currentState.merge(s)
                #t.end = self.currentState.index
                log.debug("The state is not exactly as expected.")
                if not self.forceTrigger:
                    self.toTrigger = []
            elif comp == z.Comparison.LESS:
                #self.currentState.merge(s)
                #t.end = self.currentState.index
                log.debug("The state is less complex than expected.")
                if not self.forceTrigger:
                    self.toTrigger = []
            elif comp == z.Comparison.MORE:
                #s.merge(self.currentState)
                #t.end = self.currentState.index
                log.debug("The state is more complex than expected.")
                if not self.forceTrigger:
                    self.toTrigger = []
            elif comp == z.Comparison.DIFFERENT:
                # Then the automaton is incorrect...
                return False
        self.previousState.adaptTransitionsPriority(t)

        return True

    @chronom.chronomethod
    def exploreAutomaton(self):
        """ Find and trigger as many transitions as it can """
        while not self.fullyBrowsed and not self.stop:
            if not self.trigger():
                log.debug("Incorrect automaton... go on...")
                # Stop ?
        self.save()

    @chronom.chronomethod
    def checkRelaunch(self):
        """ Check if the application has closed. Relaunch it if necessary """
        current_package = self.getRunningPackage()
        if current_package is None:
            return True # That happened with the Twitter app
        while current_package != self.package_name:
            log.debug('Left application.')
            print( current_package + " - " + self.package_name )
            log.debug('Relaunching app...')
            self.device.app_manager.start_activity( self.package_name
                                                  , self.entry_activity )
            self.waitPackage()
            current_package = self.getRunningPackage()
            return True
        return False

    @chronom.chronomethod
    def getRunningPackage(self):
        """ Returns the active package on the device """
        return self.device_ui.info.get(u'currentPackageName', None)

    @chronom.chronomethod
    def save(self):
        """ Save the context and the triggered transitions in default logs """
        # Save the states
        contextFile = self.output_dir + "/context"
        log.info("Saving context in " + contextFile)
        c = z.Context()
        c.saveTo( contextFile )

        # Save the triggered transitions
        transiFile = self.output_dir + "/triggered"
        log.info("Saving triggered transitions in " + transiFile)
        f = open( transiFile, "w" )
        f.write( "[\n" )
        first = True
        for t in self.triggered:
            if first:
                first = False
            else:
                f.write(",\n")
            f.write("# From state " + str(t.origin) + "\n")
            f.write("z." + t.toString() + "\n")
        f.write("]")
        f.close()

    @chronom.chronomethod
    def waitPackage(self):
        """ Wait for any element on screen to be clickable """
        t = 0
        while not z.State().isPackage() and t < 10:
            time.sleep(0.2)
            t += 0.2

    @chronom.chronomethod
    def loadTransitions(self,trigger):
        """ Recovers the transition log, and put it in toTrigger """
        f = open( trigger, "r" )
        s = f.read()
        self.toTrigger = eval(s)
        self.forceTrigger = True



    # --- These functions are taken from GroddRunner (first version) ---

    @chronom.chronomethod
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

    @chronom.chronomethod
    def handle_entry_points(self):
        """ Load main and entry activity according to manifest info and given
        entry point. """
        self._find_main_activity()
        self._find_entry_activity()

    @chronom.chronomethod
    def _find_main_activity(self):
        """ Set self.main_activity to an appropriate activity or exit if it
        simply can't. """
        main_activity = self.manifest.get_main_activity()
        if main_activity is not None:
            self.main_activity = main_activity.name
        else:
            quit("No activity available.")

    @chronom.chronomethod
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

    @chronom.chronomethod
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

    @chronom.chronomethod
    def start_looping(self):
        """ Launch the execution of the application """
        self.device.app_manager.start_activity( self.package_name
                                              , self.entry_activity )

        time.sleep(1)
        self.waitPackage()

        # Loads the first state
        self.currentState = z.State.insert( z.State() )
        self.initialState = self.currentState
        self.previousState = None

        print('Start discovering the app.')

        theThread = AutomatonExplorer(self)
        theThread.start()

        # By doing this, we assure that the algorithm ends in a stable state,
        # so we can properly save it, even if the process is interrupted by Ctrl-C
        # NB: Another Ctrl-C will force the process to stop
        try:
            theThread.join()
        except KeyboardInterrupt:
            self.stop = True
            log.info("Ctrl-C : Aborting...")
            theThread.join()
            raise KeyboardInterrupt()

        chronom.printMeasuredMethods()

class AutomatonExplorer(Thread):
    """ Thread that explores the automaton
    Triggering the variable Stop will try to stop the thread in a proper ay """
    def __init__(self, g):
        Thread.__init__(self)
        self.theGrodd = g

    def run(self):
        self.theGrodd.exploreAutomaton()
