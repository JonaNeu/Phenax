from uiautomator import Device
import xml.etree.ElementTree as et
import re
from enum import Enum
import time
import pickle
from branchexp.runners.key_code import writeText
import traceback # debug
import branchexp.runners.chrono_method as chronom

""" This is GroddRunner2's back-end module for manipulating the states within the automaton.

NB: Import this module from the Branchexp directory.
This way you can analyse a previous automaton from the "context" file, with some debug functions.
NB2: Don't import this module like "from state import *", otherwise Python may break the 
pacetime continuum and do strange things with globals...
NB3: Uncomment the @chronom.chronomethod lines to measure the execution time for all methods."""

# Globals & useful variables
#device = Device("0e51853e0d5cbb7e") # Default devices (for tests)
device = Device("emulator-5554")
#device = None
root = None # Root node of the element tree

# Those functions can be customized
log = print
debug = print

# Constants
MAX_SIMILAR_STATES = 5  # Max number of similar states before we consider any similar state as equal
MAX_MERGED_STATES  = 10 # Max number of merged states before we consider any similar/child state as equal

MAX_SCROLL = 5          # Max number of scroll for the same element

PRIO_CLUSTER = 100 # Prio added to transitions in the same element cluster
PRIO_SIMILAR = 200 # Prio added to transitions in the same state cluster

DEFAULT_PRIO             = 500   # Default priority for transitions
BASE_PRIO_TEXT           = 250   # Exception for text
BASE_PRIO_BACK           = 1000  # Exception for back
BASE_PRIO_WAIT           = 1500  # Exception for wait
PRIO_TEXT_AND_LONGCLICK  = 900   # Exception when an element is long-clickable and editable
PRIO_CLICK_AND_LONGCLICK = 1000  # Exception when an element is long-clickable and clickable


@chronom.chronomethod
def dump():
    """ Takes the FrameLayout UIelement as the global dump root """
    global root
    tmp = et.fromstring( device.dump() )
    for c in tmp.getchildren():
        if c.get("package") != "com.android.systemui": # We need this test for some versions of Android
            root = c
            return

class Bounds:
    """ Parses and contains the 4 bounds of an (XML) element """

    @chronom.chronomethod
    def __init__(self, x0, y0, x1, y1):
        """ Direct bounds """
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    @chronom.chronomethod
    def __init__(self, bounds_string, xOffset = 0, yOffset = 0):
        """ From XML string """
        inst = re.compile(r"""
        \[(\d+),(\d+)\]                  # x0, y0
        \[(\d+),(\d+)\]                  # x1, y1
        """, re.VERBOSE)

        match = inst.match(bounds_string)

        if match is not None:
            self.x0 = int(match.group(1)) + xOffset
            self.y0 = int(match.group(2)) + yOffset
            self.x1 = int(match.group(3)) + xOffset
            self.y1 = int(match.group(4)) + yOffset
        else:
            self.x0 = -1
            self.y0 = -1
            self.x1 = -1
            self.y1 = -1

    @chronom.chronomethod
    def update(self, bounds, xOffset, yOffset):
        """ Extends the bounds (if the XML element was not fully shown previously) """
        x0 = bounds.x0 + xOffset
        if self.x0 == -1 or x0 < self.x0:
            self.x0 = x0

        y0 = bounds.y0 + yOffset
        if self.y0 == -1 or y0 < self.y0:
            self.y0 = y0

        x1 = bounds.x1 + xOffset
        if self.x1 == -1 or x1 > self.x1:
            self.x1 = x1

        y1 = bounds.y1 + yOffset
        if self.y1 == -1 or y1 > self.y1:
            self.y1 = y1

    @chronom.chronomethod
    def compare(self,b):
        """ Arbitrary comparison mathod """
        if (self.x1 - self.x0 == b.x1 - b.x0) and (self.y1 - self.y0 == b.y1 - b.y0):
            if (self.x0 == b.x0 or self.y0 == b.y0):
                if (self.x0 == b.x0 and self.y0 == b.y0):
                    return Comparison.EQUAL
                return Comparison.SIMILAR # Same size, one coordinate is different
        n = 0
        if self.x0 == b.x0:
            n += 1
        if self.x1 == b.x1:
            n += 1
        if self.y0 == b.y0:
            n += 1
        if self.y1 == b.y1:
            n += 1
        if n >= 3:
            return Comparison.SIMILAR # Only one side is different
        return Comparison.DIFFERENT

    @chronom.chronomethod
    def midX(self):
        return (self.x0 + self.x1)/2
    
    @chronom.chronomethod
    def midY(self):
        return (self.y0 + self.y1)/2

    @chronom.chronomethod
    def sizeX(self):
        return self.x1 - self.x0

    @chronom.chronomethod
    def sizeY(self):
        return self.y1 - self.y0


class Comparison(Enum):
    """ Enumeration for different comparison degrees """
    DIFFERENT = 0
    EQUAL = 1
    SIMILAR = -1
    MORE = -2 # Similar + more elements
    LESS = -3 # Similar + less elements

    @chronom.chronomethod
    def plus(c,c2):
        """ Defines the truth table for this operation """
        if c == Comparison.DIFFERENT:
            return c1
        if c == Comparison.EQUAL:
            return c2
        if c == Comparison.SIMILAR:
            if c2 == Comparison.EQUAL or c2 == Comparison.SIMILAR:
                return Comparison.SIMILAR
            return c2
        if c == Comparison.MORE:
            if c2 == Comparison.MORE or c2 == Comparison.SIMILAR or c2 == Comparison.EQUAL:
                return Comparison.MORE
            return Comparison.DIFFERENT
        if c == Comparison.LESS:
            if c2 == Comparison.LESS or c2 == Comparison.SIMILAR or c2 == Comparison.EQUAL:
                return Comparison.LESS
        return Comparison.DIFFERENT


class StateElement:
    """ Corresponds to the XML element. Will be stored as the description of the state.
    It is already parsed from the XML string """
    @chronom.chronomethod
    def __init__( self, node, state = None, parent = None, lind = [], xOffset = 0, yOffset = 0 ):
        self.lindex = lind

        # Parse the element-tree
        self.index = (int)(node.get("index"))
        self.className = node.get("class")
        self.package = node.get("package")
        self.resId = node.get("resource-id")
        self.text = node.get("text")
        self.contentDesc = node.get("content-desc")
        self.checkable = ( node.get("checkable") == "true" )
        self.checked = ( node.get("checked") == "true" )
        self.clickable = ( node.get("clickable") == "true" )
        self.enabled = ( node.get("enabled") == "true" )
        self.focusable = ( node.get("focusable") == "true" )
        self.focused = ( node.get("focused") == "true" )
        self.scrollable = ( node.get("scrollable") == "true" )
        self.longClickable = ( node.get("long-clickable") == "true" )
        self.password = ( node.get("password") == "true" )
        self.selected = ( node.get("selected") == "true" )
        self.bounds = Bounds( node.get("bounds"), xOffset, yOffset )

        #TODO No idea how to do it better, but it works for now...
        self.editable = ( self.className == "android.widget.EditText" )

        # Useful to clusterization
        self.cluster = [self]

        self.transitions = None

        self.childCount = 0
        self.children = {}

        self.parent = parent
        if self.parent is not None:
            self.parent.childCount = max(self.parent.childCount,self.index+1)
        self.state = state

    @chronom.chronomethod
    def isVisible(self):
        """ Test if the element is visible according to the last dump """
        return isVisible(self.lindex)

    @chronom.chronomethod
    def discover(self, node = None, xOffset = 0, yOffset = 0):
        """ Discovers the element from the XML tree, scrolling if needed. """
        if self.scrollable:
            scrollToTop( self.lindex )
            node = getXmlElement( self.lindex )
            if node is None:
                # Strange... aborting
                return
            self.staticDiscover( node, xOffset, yOffset )

            nbScroll = 0
            finished = False
            while not finished:
                y = verticalScrollForward( self.lindex )
                if y == 0:
                    finished = True
                elif y == -1:
                    # Unexpected scroll...
                    return
                else:
                    yOffset += y
                    # The XML has changed, so we compute the node again
                    node = getXmlElement( self.lindex )
                    if node is None:
                        # Strange... aborting
                        return
                    self.staticDiscover( node, xOffset, yOffset )
                    nbScroll += 1
                    if nbScroll >= MAX_SCROLL:
                        finished = True
        else:
            if node is None:
                node = getXmlElement( self.lindex )
                if node is None:
                    # Strange... aborting
                    return
            self.staticDiscover(node, xOffset, yOffset)

    @chronom.chronomethod
    def staticDiscover(self, node, xOffset = 0, yOffset = 0, dontDoBottom = False):
        """ Discovers the element without scrolling """
        b = Bounds( node.get("bounds") )
        self.bounds.update( b, xOffset, yOffset )

        for c in node:
            i = int(c.get("index"))
            try:
                # Element already known
                child = self.children[i]
                child.staticDiscover(c, xOffset, yOffset)
            except KeyError:
                # New element

                # If we are scrolling, and the element is half hidden at the bottom, then don't do it
                if dontDoBottom:
                    if Bounds(c.get("bounds")).y1 == b.y1:
                        continue

                child = StateElement( c, self.state, self, self.lindex + [i], xOffset, yOffset )
                self.children[i] = child
                child.discover(c, xOffset, yOffset)

    @chronom.chronomethod
    def compare(self, s, ignoreIndex = False, DEBUG = False):
        """ Computes the comparison between 2 states according to attributes, transitions
        and children elements """
        r = Comparison.EQUAL

        # --- Compare attributes ---
        if self.index != s.index and not ignoreIndex:
            if DEBUG: # This function can show a lot of information, so we add some print statements for debug
                debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                        + "Different indices : " + str(self.index) + " VS " + str(s.index) )
            return r.DIFFERENT
        if self.className != s.className:
            if DEBUG:
                debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                        + "Different class names : " + self.className + " VS " + s.className )
            return r.DIFFERENT
        if self.package != s.package:
            if DEBUG:
                debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                        + "Different packages : " + self.package + " VS " + s.package )
            return r.DIFFERENT
        if self.resId != s.resId and not ignoreIndex:
            if DEBUG:
                debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                        + "Different ressource-id : " + self.resId + " VS " + s.resId )
            return r.DIFFERENT
        if self.text != s.text:
            if DEBUG:
                debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                        + "Different texts : " + self.text + " VS " + s.text )
            r = r.plus(r.SIMILAR)
        if self.contentDesc != s.contentDesc:
            if DEBUG:
                debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                        + "Different context-desc : " + self.contentDesc + " VS " + s.contextDesc )
            r = r.plus(r.SIMILAR)
        if self.checked != s.checked:
            if DEBUG:
                debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                        + "Different checked : " + str(self.checked) + " VS " + str(s.checked) )
            r = r.plus(r.SIMILAR)
        if self.enabled != s.enabled:
            if DEBUG:
                debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                        + "Different enabled : " + str(self.enabled) + " VS " + str(s.enabled) )
            if self.enabled:
                r = r.plus( r.MORE )
            else:
                r = r.plus( r.LESS )
            if r == r.DIFFERENT:
                return r.DIFFERENT
        if self.selected != s.selected:
            r = r.plus(r.SIMILAR)
        if self.password != s.password:
            if DEBUG:
                debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                        + "Different password : " + str(self.password) + " VS " + str(s.password) )
            r = r.plus(r.SIMILAR)
        if self.enabled and s.enabled: # Otherwise, it is pointless to compare the following attributes
            if self.checkable != s.checkable:
                if DEBUG:
                    debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                            + "Different checkable : " + str(self.checkable) + " VS " + str(s.checkable) )
                if self.checkable:
                    r = r.plus( r.MORE )
                else:
                    r = r.plus( r.LESS )
                if r == r.DIFFERENT:
                    return r.DIFFERENT
            if self.clickable != s.clickable:
                if DEBUG:
                    debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                            + "Different clickable : " + str(self.clickable) + " VS " + str(s.clickable) )
                if self.clickable:
                    r = r.plus( r.MORE )
                else:
                    r = r.plus( r.LESS )
                if r == r.DIFFERENT:
                    return r.DIFFERENT
            if self.focusable != s.focusable:
                if DEBUG:
                    debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                            + "Different focusable : " + str(self.focusable) + " VS " + str(s.focusable) )
                if self.focusable:
                    r = r.plus( r.MORE )
                else:
                    r = r.plus( r.LESS )
                if r == r.DIFFERENT:
                    return r.DIFFERENT
            if self.scrollable != s.scrollable:
                if DEBUG:
                    debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                            + "Different scrollable : " + str(self.scrollable) + " VS " + str(s.scrollable) )
                if self.scrollable:
                    r = r.plus( r.MORE )
                else:
                    r = r.plus( r.LESS )
                if r == r.DIFFERENT:
                    return r.DIFFERENT
            if self.longClickable != s.longClickable:
                if DEBUG:
                    debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                            + "Different long-clickable : " + str(self.longClickable) + " VS " + str(s.longClickable) )
                if self.longClickable:
                    r = r.plus( r.MORE )
                else:
                    r = r.plus( r.LESS )
                if r == r.DIFFERENT:
                    return r.DIFFERENT

        # We don't compare the "focused" attribute

        # Finally, we don't compare bounds... But we could !
        # r = r.plus( self.bounds.compare(s.bounds) )

        # --- Compare transitions ---
        if self.transitions is not None and s.transitions is not None:
            for t1 in self.transitions:
                t2 = s.getDirectTransition(t1)
                if t2 is None:
                    #r = r.plus(r.MORE)
                    if DEBUG:
                        debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                                + "More transitions for first element" )
                    if r == r.DIFFERENT:
                        return r.DIFFERENT
                else:
                    comp = t1.compare(t2, ignoreIndex = True)
                    if comp == r.DIFFERENT:
                        if DEBUG:
                            debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                                    + "Different transitions for " + t1.toDebugString() )
                        return r.DIFFERENT

            for t2 in s.transitions:
                t1 = s.getDirectTransition(t2)
                if t1 is None:
                    #r = r.plus(r.LESS)
                    if DEBUG:
                        debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                                + "More transitions for second element" )
                    if r == r.DIFFERENT:
                        return r.DIFFERENT
                else:
                    comp = t1.compare(t2, ignoreIndex = True)
                    if comp == r.DIFFERENT:
                        if DEBUG:
                            debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                                    + "Different transitions for " + t1.toDebugString() )
                        return r.DIFFERENT

        # --- Compare children ---
        for i, c in self.children.items():
            try:
                r = r.plus( c.compare( s.children[i], DEBUG=DEBUG ) )
            except KeyError:
                r = r.plus( r.MORE )
                if DEBUG:
                    debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                            + "One more child in first element")
            if r == r.DIFFERENT:
                return r.DIFFERENT

        for i in s.children.keys():
            if not i in self.children.keys():
                r = r.plus( r.LESS )
                if DEBUG:
                    debug( "(" + str(self.lindex) + "-" + str(s.lindex) + ") "
                            + "One more child in second element")
            if r == r.DIFFERENT:
                return r.DIFFERENT

        return r

    @chronom.chronomethod
    def setVisible(self, l):
        """ Recursively scrolls elements so that the element designated by l is visible """
        if not l:
            return

        h, *t = l
        target = self.children[h]

        if self.scrollable:
            # Find the actual position
            node = getXmlElement(self.lindex)
            c = node[0]
            i = int(c.get("index"))
            b = Bounds( node.get("bounds") )
            bc = Bounds( c.get("bounds") )
            if b.y0 == bc.y0:
                currentOffset = self.children[i].bounds.y1 - bc.y1
            else:
                currentOffset = self.children[i].bounds.y0 - bc.y0

            # Scrolls in the good direction until the targetted child is fully shown
            btarget = target.bounds
            while btarget.y0 < b.y0 + currentOffset or \
                    btarget.y1 > b.y1 + currentOffset:
                if btarget.y0 < b.y0 + currentOffset:
                    currentOffset -= verticalScrollBackward( self.lindex )
                else:
                    currentOffset += verticalScrollForward( self.lindex )

        # Repeats for the child
        target.setVisible(t)

    def listElements(self):
        """ For debug : prints all lindex of children elements """
        debug(self.lindex)
        for c in self.children.values():
            c.listElements()

    @chronom.chronomethod
    def getElement(self,l):
        """ Get the element designated by l """
        if not l:
            return self
        h, *t = l
        try:
            return self.children[h].getElement(t)
        except KeyError:
            return None

    @chronom.chronomethod
    def clusterize(self):
        """ Regroups similar children inside clusters
        The SIMILAR relation is an equivalence relation, so we can deduce equivalence classes """
        for i1, c1 in self.children.items():
            for i2, c2 in self.children.items():
                if i1 != i2:
                    comp = c1.compare(c2,ignoreIndex=True)
                    if (comp == Comparison.SIMILAR or comp == Comparison.EQUAL) and c1 not in c2.cluster:
                        # Merge clusters
                        tmpCluster = c2.cluster
                        c1.cluster += tmpCluster
                        for c in tmpCluster:
                            c.cluster = c1.cluster
        for c in self.children.values():
            c.clusterize()

    @chronom.chronomethod
    def addTransition(self,t):
        """ Just add a transition to this element.
        The same transition is also referenced in the state attribute """
        self.transitions.append(t)
        self.state.transitions.append(t)

    @chronom.chronomethod
    def constructTransitions(self):
        """ Build appropriate transitions """
        self.transitions = []

        n = self.state.index
        if self.enabled:
            if self.editable:
                self.addTransition( Text(self.lindex, origin = n, prio = BASE_PRIO_TEXT) )
                self.addTransition( LongClick(self.lindex, origin = n, prio = PRIO_TEXT_AND_LONGCLICK) )
            else:
                if self.clickable or self.checkable:
                    self.addTransition( Click(self.lindex, origin = n) )
                    if self.longClickable:
                        self.addTransition( LongClick(self.lindex, origin = n, prio = PRIO_CLICK_AND_LONGCLICK) )
                else:
                    if self.longClickable:
                        self.addTransition( LongClick(self.lindex, origin = n) )

        if self.parent is None:
            self.addTransition( Back( origin = n, prio = BASE_PRIO_BACK ) )
            self.addTransition( Wait( origin = n, prio = BASE_PRIO_WAIT ) )

        for c in self.children.values():
            c.constructTransitions()

    @chronom.chronomethod
    def merge(self,s):
        """ Only need to merge transitions """
        if self.transitions is None:
            self.transitions = s.transitions
        else:
            if s.transitions is not None:
                for t in self.transitions:
                    t2 = s.getDirectTransition(t)
                    if t2 is not None:
                        t.merge(t2)

        for i,c in self.children.items():
            c.merge( s.children[i] )

    @chronom.chronomethod
    def getDirectTransition(self,t):
        """ Get the transition corresponding to t (only in this element) """
        for t1 in self.transitions:
            if t.compare(t1,ignoreIndex=True) != Comparison.DIFFERENT:
                return t1
        return None

    @chronom.chronomethod
    def isPackage(self):
        """ Just test if at least one element is clickable... """
        if self.clickable:
            return True
        for c in self.children.values():
            if c.isPackage():
                return True
        return False

    @chronom.chronomethod
    def removeTransitions(self):
        """ Destructs transitions """
        self.transitions = None
        for c in self.children.values():
            c.transitions = None



class State:
    """ Defines an activity for the automaton """
    nbOfStates = 0 # Nb of states created
    states = None # List of states
    remainingStates = None # List of indices of states remaining after merge
    root = None # Must create after class definitions

    @chronom.chronomethod
    def __init__(self):
        dump() # This is where the dump is done un GroddRunner2 !

        self.transitions = []
        self.index = None

        self.root = StateElement( root, self )
        self.root.discover()

        self.parent = None
        self.children = None
        self.similar = [self] # 
        self.merged = [] # None if there are too many similmar states merged

    @chronom.chronomethod
    def compare(self, s, DEBUG=False):
        """ Compares the element trees """
        comp = self.root.compare(s.root,DEBUG=DEBUG)
        if comp != Comparison.DIFFERENT:
            # Too many states merged... we consider all similar states as equal
            if self.merged is None:
                return Comparison.EQUAL
            for s2 in self.merged:
                if s2.compare(s.root,DEBUG=DEBUG) == Comparison.EQUAL:
                    return Comparison.EQUAL
        return comp

    @chronom.chronomethod
    def getElement(self,l):
        """ Gets the element from its lindex """
        return self.root.getElement(l)

    @chronom.chronomethod
    def getTransition(self,t):
        """ Gets the similar transition in this state """

        # It is more optimized to take it from the corresponding element rather than looking for it
        # in the whole list of transitions
        e = self.getElement(t.lindex)
        if e is None:
            return None
        return e.getDirectTransition( t )

    @chronom.chronomethod
    def setVisible(self,l):
        """ Perform the scrolls needed to set the element visible """
        self.root.setVisible(l)

    @chronom.chronomethod
    def listElements(self):
        """ Mainly for debug. Lists the lindex of all the elements """
        self.root.listElements()

    @chronom.chronomethod
    def removeTransitions(self):
        """ Destruct transitions """
        self.transitions = None
        self.root.removeTransitions()

    @chronom.chronomethod
    def merge(self, s):
        """ Merge self and s into self.
        self takes all possible information from s.
        After merging, if we look for s in the state tree, we find self """
        if s.index is not None and self.index != s.index:
            debug("Merging state " + str(self.index) + " and state " + str(s.index))
            self.states[s.index] = self
            self.root.merge(s.root)
            self.merged += s.merged
            self.merged.append(s.root)

            # Too many states merged. Since now, we consider all similar state as equal...
            if len(self.merged) >= MAX_MERGED_STATES:
                self.merged = None

            try:
                if self.similar is not None:
                    self.similar.remove(s)
            except ValueError:
                pass
            
            s.removeTransitions()

            State.remainingStates.remove(s.index)

            # If s is already in the tree
            # Then re-insert children of s after removing it
            if s.parent is not None:
                State.states[s.parent].children.remove(s)
                theParent = None
                for c in s.children:
                    if theParent is None:
                        theParent = State.states[ State.insertIntoTree(c,State.states[self.parent]).parent ]
                    else:
                        State.insertIntoTree(c,theParent)



    @staticmethod
    @chronom.chronomethod
    def insert(s):
        """ Once the state is discovered, you want to add it to the global state tree.
        Then construct the transitions and element clusters if needed.
        Returns the state according to what already exists. """

        # Insert it into the tree
        treeState = State.insertIntoTree( s )

        # If the state was not already in the tree
        if treeState.index is None:
            # Add it to the dicionary
            State.nbOfStates += 1
            s.index = State.nbOfStates
            State.states.append(s)
            State.remainingStates.append(s.index)

            s.root.constructTransitions()
            s.root.clusterize()
            s.initTransitionsPriority()

        return treeState

    @staticmethod
    @chronom.chronomethod
    def insertIntoTree( s1, s2 = None ):
        """ Insert the state s1 in the global state tree (if needed).
        Returns the inserted state, or the already existing state """
        if s2 is None:
            s2 = State.root

        s1.children = []
        s1.similar = [s1]

        lchildren = []
        tmpSimilar = None
        for s in s2.children:
            comp = s1.compare(s)
            if comp == Comparison.EQUAL:
                s.merge(s1)
                return s
            if comp == Comparison.MORE:
                return State.insertIntoTree(s1,s)
            if comp == Comparison.LESS:
                lchildren.append(s)
                continue
            if comp == Comparison.SIMILAR:
                if s.similar is None or s1.similar is None:
                    s1.similar = None # Similar cluster broken
                else:
                    tmpSimilar = s.similar # The similar cluster is not broken
                    if not tmpSimilar:
                        # If there was already too many states in this similar cluster
                        s.merge(s1)
                        return s

        if tmpSimilar is not None:
            s1.similar = tmpSimilar
            tmpSimilar.append(s1) # Add s1 to the cluster (if there is no equal state)
            if len(tmpSimilar) >= MAX_SIMILAR_STATES:
                # Too many similar states. Forcing the merge of all similar states
                for s in tmpSimilar:
                    s1.merge(s)
                tmpSimilar[:] = []
                return s1

        # If s1 is a parent, then move the concerned states as children of s
        if lchildren:
            for c in lchildren:
                s2.children.remove(c)
                if s1.index is None:
                    c.parent = State.nbOfStates+1
                else:
                    c.parent = s1.index
            s1.children = lchildren
        s2.children.append(s1)
        s1.parent = s2.index
        return s1

    @staticmethod
    @chronom.chronomethod
    def init():
        """ Static method to remove existing states and reset the global state tree  """
        State.root = RootState()
        State.states = [State.root]
        State.remainingStates = []

    @staticmethod
    @chronom.chronomethod
    def mergeAllSimilarTrees( r = None ):
        """ Merge all that can be merged... never used so far """
        if r is None:
            r = State.root

        # List of indices, so we are sure not to mistake with the children list...
        l = []
        for s in r.children:
            i = s.index
            if i not in l:
                l.append(i)

        # Merging if the states are not the same, but similar
        for i in l:
            for j in l:
                s1 = State.states[i]
                s2 = State.states[j]
                if s1.index != s2.index and s1.compare(s2) == Comparison.SIMILAR:
                    s1.merge(s2)

    @chronom.chronomethod
    def initTransitionsPriority(self):
        """ Add priority to similar/child/parent states and adapt its own priorities,
        when self has just been added to the state tree """
        #TODO Perhaps it should not add priority, just adapt it...
        if self.similar:
            for s in self.similar:
                if s.index != self.index:
                    for t in self.transitions:
                        t2 = s.getTransition(t)
                        t2.addPrio(1)
                        t.adaptPrio( t2 )
        if self.children:
            for c in self.children:
                for t in self.transitions:
                    t2 = c.getTransition(t)
                    t2.addPrio(1)
                    t.adaptPrio( t2 )
        elif self.parent:
            c = State.states[self.parent]
            for t in self.transitions:
                t2 = c.getTransition(t)
                if t2 is not None:
                    t2.addPrio(1)
                    t.adaptPrio(t2)

    @chronom.chronomethod
    def adaptTransitionsPriority(self, t, allowParent = True, allowChildren = True, allowSimilar = True):
        """ When you trigger a transition and you want to change priority of
        similar/cluster/parent transitions """

        # With these 3 booleans, we can browse the state cluster through the tree
        # with top, bottom, and lateral movements.
        # This way, there should not be any recursion loop

        tself = self.getTransition(t)
        if tself is None:
            return
        tself.addPrio( PRIO_SIMILAR )

        fullDisco = self.isFullyDiscovered()

        # --- Clusters ---
        cluster = self.getElement(t.lindex).cluster
        # First, test if the cluster is still correct
        correct = True
        for e in cluster:
            t1 = e.getDirectTransition(t)
            if t.compare(t1,ignoreIndex=True) == Comparison.DIFFERENT:
                correct = False
                break

        # If it is still correct, add some prio
        if correct:
            for e in cluster:
                t2 = e.getDirectTransition(t)
                if t2 is not tself: # For similar states, tself should not be affected twice
                    t2.addPrio( PRIO_CLUSTER )
        # Else, break the cluster
        else:
            ttt = "Breaking element cluster"
            for e in cluster:
                e.cluster = [e]
                for t1 in e.transitions:
                    t1.resetPrio()
                    ttt += "\n  " + t1.toDebugString()
            debug(ttt)
        #TODO Also break clusters of similar states ?

        # --- Similar states ---
        if self.similar is not None:
            # First, tests if the states are still similar
            # (Can be optimized, if you only take in account the new transition for the comparison)
            tmpSimilar = list(self.similar)
            correct = True
            for s in tmpSimilar:
                if s.index != self.index:
                    t2 = s.getTransition(t)
                    if t.compare(t2) == Comparison.DIFFERENT:
                        correct = False
                        break

            # If it is still correct, apply on the similar states
            if correct and allowSimilar:
                for s in tmpSimilar:
                    if s.index != self.index:
                        if fullDisco and s.isFullyDiscovered():
                            # This behaviour can be dangerous...
                            self.merge(s) # No need to keep 2 different states
                        else:
                            s.adaptTransitionsPriority(t, allowSimilar = False, allowParent = False)
            # Else, break the similar lists
            else:
                if not correct:
                    ttt = "Breaking state cluster "
                    lll = []
                    for s in tmpSimilar:
                        lll.append(s.index)
                    ttt += str(lll)
                    debug( ttt )

                    for s in tmpSimilar:
                        s.similar = None

        # --- Child transitions ---
        if allowChildren:
            tmpChildren = list(self.children)
            for c in tmpChildren:
                t2 = c.getTransition(t)
                if t2 is None or t.compare(t2) == Comparison.DIFFERENT:
                    # The child is incorrect. Reinsert it
                    self.children.remove(c)
                    State.insert(c)
                else:
                    if fullDisco and c.isFullyDiscovered():
                        # This behaviour can be dangerous...
                        self.merge(c) # No need to keep 2 different states
                    else:
                        c.adaptTransitionsPriority(t, allowParent = False, allowSimilar = False)

        # --- Parent transitions ---
        if allowParent and self.parent is not None:
            parent = State.states[self.parent]
            t2 = parent.getTransition(t)
            if t2 is not None:
                if t.compare(t2) == Comparison.DIFFERENT:
                    # This element is not a child anymore... reinsert it
                    parent.children.remove(self)
                    State.insert(self)
                else:
                    if fullDisco and parent.isFullyDiscovered():
                        # This can be dangerous to automatically merge !
                        parent.merge(self) # No need to keep 2 different states
                    else:
                        parent.adaptTransitionsPriority(t, allowChildren = False)

    @chronom.chronomethod
    def isPackage(self):
        """ Check for any clickable element """
        return self.root.isPackage()

    @chronom.chronomethod
    def isFullyDiscovered(self):
        """ Returns if all transitions have been triggered """
        if self.transitions:
            for t in self.transitions:
                if t.end is None:
                    return False
        return True

    @staticmethod
    @chronom.chronomethod
    def getTreeStates(s=None,l=[]):
        """ For debug : list all remaining states and their index in the tree """
        if s is None:
            s = State.root
        debug(l)
        
        for c in s.children:
            State.getTreeStates(c, l+[c.index])

    def isSimilar(self, s, allowParent = True, allowSimilar = True, allowChildren = True):
        """ According to the tree structure """
        #TODO This method should be verified, I think it is not working perfectly...
        if self.index == s.index:
            return True
        if allowSimilar:
            if not self.similar or not s.similar:
                return False
            if s in self.similar:
                return True
        if allowParent:
            p = State.states[self.parent]
            if p.isSimilar(s,allowChildren=False):
                return True
        if allowChildren:
            for c in self.children:
                if c.isSimilar(s,allowParent=False,allowSimilar=False):
                    return True
        return False

class RootState(State):
    """ Empty state, root of the global state tree """
    @chronom.chronomethod
    def __init__(self):
        self.index = 0
        self.parent = None
        self.children = []
        self.similar = []

        self.root = None

    @chronom.chronomethod
    def compare(self, s):
        return Comparison.MORE

    @chronom.chronomethod
    def adaptTransitionsPriority(self, t,allowChildren=True,allowParent=True,allowSimilar=True):
        return

    @chronom.chronomethod
    def getTransition(self,t):
        return None

    @chronom.chronomethod
    def getElement(self,l):
        return None

    @chronom.chronomethod
    def merge(self,s):
        return

    @chronom.chronomethod
    def isSimilar(self,s,allowChildren=True,allowParent=True,allowSimilar=True):
        return False


class Transition:
    """ Base class for all transitions/actions on the states """
    @chronom.chronomethod
    def __init__(self, l = [], origin = None, end = None, prio = DEFAULT_PRIO, *args, **kwargs):
        self.lindex = l
        self.prio = prio
        self.basePrio = prio

        # Origin and final states for this transition (indices only)
        self.origin = origin
        self.end = end

    @chronom.chronomethod
    def addPrio(self, p):
        """ Just add priority.
        The higher the prio attribute is, the less priority it is... """
        self.prio = self.prio + p

    @chronom.chronomethod
    def resetPrio(self):
        """ Reset the prio attribute to its first value """
        self.prio = self.basePrio

    @chronom.chronomethod
    def adaptPrio(self, t):
        """ Take the maximum of the prio attribute """
        if self.prio > t.prio:
            t.prio = self.prio
        else:
            self.prio = t.prio

    @staticmethod
    @chronom.chronomethod
    def fromString( s ):
        """ Create a Transition object from the toString result """
        return eval(s)

    @chronom.chronomethod
    def args(self):
        """ Use this method to add new arguments to pass to the constructor in derived classes """
        return ""

    @chronom.chronomethod
    def com(self):
        """ Use this method to add a commentary in the transitions log in derived classes """
        return ""

    @chronom.chronomethod
    def toString(self):
        """ Readable and modifyable string to store in the trigger log """
        txt = self.__class__.__name__ + "( l = " + str(self.lindex)
        a = self.args()
        if a != "":
            txt += ",\n    " + a
        txt += " )"
        txt += self.com()
        return txt

    @chronom.chronomethod
    def toDebugString(self):
        """ Format the description for the debug log """
        txt = "{:9}".format(self.__class__.__name__) + " "
        txt += "{:8}".format(str(self.lindex)) + " : "
        txt += "{:>3}".format(str(self.origin)) + " -> "
        if self.end is None:
            txt += "XXX"
        else:
            txt += "{:>3}".format(str(self.end))
        if self.end is None:
            txt += " (" + str(self.prio) + ")"
        return txt


    @chronom.chronomethod
    def compare(self,t,ignoreIndex = False):
        """ Arbitrary comparison between self and t """
        if self.__class__ != t.__class__:
            return Comparison.DIFFERENT
        if not ignoreIndex and self.lindex != t.lindex:
            return Comparison.DIFFERENT
        # We don't compare origins
        if self.end is not None and t.end is not None:
            if self.end != t.end:
                s1 = State.states[self.end]
                s2 = State.states[t.end]
                # We don't deeply compare the states (recursion loop !)
                # We rather use the existing tree structure
                if s1.isSimilar(s2):
                    return Comparison.SIMILAR
                return Comparison.DIFFERENT
        return Comparison.EQUAL

    @chronom.chronomethod
    def merge(self,t):
        """ Merges transitions (only the endpoint)
        NB: When merging states, we take the endpoint of the deleting state
        This way, the endpoint state will be more likely to merge ! """
        if t.end is not None:
            if self.end is not None:
                if self.end != t.end:
                    s1 = State.states[self.end]
                    s2 = State.states[t.end]
                    comp = s1.compare(s2)
                    if comp == Comparison.LESS:
                        self.end = t.end
            else:
                self.end = t.end
        self.adaptPrio(t)

class Click(Transition):
    """ Simple click on an element """
    @chronom.chronomethod
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @chronom.chronomethod
    def trigger(self):
        node = getXmlElement(self.lindex)
        if node is None:
            # Problem with the element...
            debug( "Problem with the element " + str(self.lindex) )
            return
        bounds = Bounds( node.get("bounds") )
        x = bounds.midX()
        y = bounds.midY()
        device.click(x,y)

class ClickBack(Transition):
    """ Click then back, in one transition """
    @chronom.chronomethod
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @chronom.chronomethod
    def trigger(self):
        node = getXmlElement(self.lindex)
        if node is None:
            # Problem with the element...
            debug( "Problem with the element " + str(self.lindex) )
            return
        bounds = Bounds( node.get("bounds") )
        x = bounds.midX()
        y = bounds.midY()
        device.click(x,y)
        time.sleep(0.5)
        device.press.back()

class LongClick(Transition):
    """ Long click on an element """
    @chronom.chronomethod
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @chronom.chronomethod
    def trigger(self):
        node = getXmlElement(self.lindex)
        if node is None:
            # Problem with the element...
            debug( "Problem with the element " + str(self.lindex) )
            return
        bounds = Bounds( node.get("bounds") )
        x = bounds.midX()
        y = bounds.midY()
        device.long_click(x,y)

class Back(Transition):
    """ Press the Back button """
    @chronom.chronomethod
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @chronom.chronomethod
    def trigger(self):
        device.press.back()

class Text(Transition):
    """ Enter text in a text field
    You can modify the text content in the trigger log if you want to load it again """
    @chronom.chronomethod
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.text = kwargs["text"]
        except KeyError:
            #TODO generate random text
            self.text = "grodd"

    @chronom.chronomethod
    def trigger(self):
        # Click
        node = getXmlElement(self.lindex)
        if node is None:
            # Problem with the element...
            debug( "Problem with the element " + str(self.lindex) )
            return
        bounds = Bounds( node.get("bounds") )
        x = bounds.midX()
        y = bounds.midY()
        device.click(x,y)

        # Ctrl-A, Del
        device.press(0x1d, 0x1000)
        device.press("del")

        # Write the text char by char
        #writeText(device,self.text) # This method does not fully work
        device(focused="true").set_text(self.text) # This method is unsure

        #device.press.back()

    @chronom.chronomethod
    def args(self):
        return "text = \"" + self.text + "\""

    @chronom.chronomethod
    def com(self):
        return "   # <-- You can customize this text"

class Wait(Transition):
    """ Wait for some time """
    @chronom.chronomethod
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.time = int(kwargs["time"])
        except KeyError:
            #TODO generate random text
            self.time = 3

    @chronom.chronomethod
    def trigger(self):
        time.sleep(self.time)

    @chronom.chronomethod
    def args(self):
        return "time = " + str(self.time)

    @chronom.chronomethod
    def com(self):
        return "   # <-- You can customize this waiting time"



@chronom.chronomethod
def isVisible( l, node = None ):
    """ Test if the element indicated by the index list is in the current dump """
    global root
    if node is None:
        node = root

    if not l:
        return True

    h, *t = l
    for c in node:
        if (int)(c.get("index")) == h:
            return isVisible( t, c )
    return False

@chronom.chronomethod
def getXmlElement( l, node = None ):
    """ Gets the node from the index list """
    global root
    if node is None:
        node = root

    if not l:
        return node
 
    h, *t = l
    for c in node:
        if (int)(c.get("index")) == h:
            return getXmlElement( t, c )

    return None

@chronom.chronomethod
def getVisibleElements( l = [], node = None ):
    """ Get a list of lindex of all visible elements in the current dump """
    global root
    if node is None:
        node = root

    if not l:
        ret = []
    else:
        ret = [l]

    for c in node:
        lc = l + [int(c.get("index"))]
        ret += getVisibleElements( lc, c )
    return ret

@chronom.chronomethod
def verticalScrollForward( l, steps=60 ):
    """ Scroll forward of (approximately) half of the size of the element
    Returns the number of pixels it has scrolled of """
    e = getXmlElement(l)
    bounds = Bounds(e.get("bounds"))

    # 2 points for the gesture
    x = bounds.midX()
    y1 = bounds.midY()
    y2 = y1
    y1 -= bounds.sizeY() / 4
    y2 += bounds.sizeY() / 4

    # If there is a scrollable element in this element, and it is at the first position for the drag,
    # then find a better position
    botElementIndex = scrollableChild(x,y2,l)
    firstBotElement = botElementIndex
    # Moving first position towards bot
    while botElementIndex is not None:
        y2 = Bounds( getXmlElement(botElementIndex).get("bounds") ).y0 - 1
        botElementIndex = scrollableChild(x,y2,l)
    if y1 >= y2 - 25:
        y1 = Bounds( getXmlElement([0]).get("bounds") ).y0
        if y1 >= y2 - 25:
            # If not sufficent, towards top
            botElementIndex = firstBotElement

            while botElementIndex is not None:
                y2 = Bounds( getXmlElement(botElementIndex).get("bounds") ).y1 + 1
                botElementIndex = scrollableChild(x,y2,l)

            if y1 >= y2 - 25:
                log("Can't scroll !")
                return 0

    # List of bottom bounds of children
    lbot = []
    for c in e:
        i = (int)(c.get("index"))
        b = Bounds(c.get("bounds"))
        lbot.append( (i,b.y1) )

    # Do the scroll (supposed to be one half of the vert size)
    device.drag( x, y2, x, y1, steps=steps )

    # Recreates the list of bottom bounds
    dump()
    e = getXmlElement(l)
    lbot2 = []
    for c in e:
        i = (int)(c.get("index"))
        b = Bounds(c.get("bounds"))
        lbot2.append( (i,b.y1) )

    # Compares the bounds and takes the max
    theMax = -1
    for (i1, b1) in lbot:
        for(i2, b2) in lbot2:
            if i1 == i2:
                theMax = max(theMax, b1-b2)
                break

    return theMax


@chronom.chronomethod
def verticalScrollBackward( l, steps=60 ):
    """ Same for backward scrolling """
    e = getXmlElement(l)
    bounds = Bounds(e.get("bounds"))

    # 2 points for the gesture
    x = (bounds.x0 + bounds.x1) / 2
    y1 = (bounds.y0 + bounds.y1) / 2
    y2 = y1
    y1 -= (bounds.y1 - bounds.y0) / 4
    y2 += (bounds.y1 - bounds.y0) / 4

    # If there is a scrollable element in this element, and it is at the wrong position,
    # then find a better position
    topElementIndex = scrollableChild(x,y1,l)
    firstTopElement = topElementIndex
    while topElementIndex is not None:
        y1 = Bounds( getXmlElement(topElementIndex).get("bounds") ).y1 + 1
        topElementIndex = scrollableChild(x,y1,l)
    if y1 >= y2 - 25:
        y2 = Bounds( getXmlElement([0]).get("bounds") ).y1
        if y1 >= y2 - 25:
            topElementIndex = firstTopElement
            while topElementIndex is not None:
                y1 = Bounds( getXmlElement(topElementIndex).get("bounds") ).y0 - 1
                topElementIndex = scrollableChild(x,y1,l)

            if y1 >= y2 - 25:
                log("Can't scroll !")
                return 0

    # List of bottom bounds of children
    ltop = []
    for c in e:
        i = (int)(c.get("index"))
        b = Bounds(c.get("bounds"))
        ltop.append( (i,b.y0) )

    # Do the scroll (supposed to be one half of the vert size)
    device.drag( x, y1, x, y2, steps=steps )

    # Recreates the list of bottom bounds
    dump()
    e = getXmlElement(l)
    if e is None:
        log("This scroll is unexpected...")
        return -1
    ltop2 = []
    for c in e:
        i = (int)(c.get("index"))
        b = Bounds(c.get("bounds"))
        ltop2.append( (i,b.y0) )

    # Compares the bounds and takes the max
    theMax = -1
    for (i1, b1) in ltop:
        for(i2, b2) in ltop2:
            if i1 == i2:
                theMax = max(theMax, b2-b1)
                break

    return theMax

@chronom.chronomethod
def scrollToBottom(l):
    """ Scroll forward until it reaches the bottom, or it detects a loop """
    llc = []
    lc = []
    e = getXmlElement(l)
    if e is None:
        # Unexpected scroll...
        return
    for c in e:
        b = Bounds(c.get("bounds"))
        lc.append( (int(c.get("index")), b.y0, b.y1) )
    llc.append( lc )

    nbScroll = 0

    while verticalScrollForward(l,10) != 0:
        lc = []
        e = getXmlElement(l)
        if e is None:
            # Unexpected scroll...
            return
        for c in e:
            b = Bounds(c.get("bounds"))
            lc.append( (int(c.get("index")), b.y0, b.y1) )
        if lc in llc:
            # Detects a cycle...
            return
        llc.append( lc )
        nbScroll += 1
        if nbScroll >= MAX_SCROLL:
            return

@chronom.chronomethod
def scrollToTop(l):
    """ Scroll backward until it reaches the top, or it detects a loop """
    llc = []
    lc = []
    e = getXmlElement(l)
    if e is None:
        # Unexpected scroll...
        return
    for c in e:
        b = Bounds(c.get("bounds"))
        lc.append( (int(c.get("index")), b.y0, b.y1) )
    llc.append( lc )

    nbScroll = 0

    while verticalScrollBackward(l,10) != 0:
        lc = []
        e = getXmlElement(l)
        if e is None:
            # Unexpected scroll...
            return
        for c in e:
            b = Bounds(c.get("bounds"))
            lc.append( (int(c.get("index")), b.y0, b.y1) )
        if lc in llc:
            # Detects a cycle
            return
        llc.append( lc )
        nbScroll += 1
        if nbScroll >= MAX_SCROLL:
            return

@chronom.chronomethod
def scrollableChild(x,y,l,e = None):
    """ Finds a child of l that is scrollable.
    Useful when there is a scrollable element in another scrollable element """
    if e is None:
        e = getXmlElement(l)
        if e is None:
            # Unexpected scroll...
            return None
    else:
        bounds = Bounds( e.get("bounds") )
        if x < bounds.x0 or x > bounds.x1 or y < bounds.y0 or y > bounds.y1:
            return None
        if e.get("scrollable") == "true" or e.get("long-clickable") == "true" or e.get("class") == "android.widget.EditText":
            return l

    for c in e:
        lc = l + [int(c.get("index"))]
        ret = scrollableChild(x,y,lc,c)
        if ret is not None:
            return ret
    return None

class Context:
    """ Useful to serialize/deserialize the state tree, etc... """
    @chronom.chronomethod
    def __init__(self):
        self.states = State.states
        self.root = State.root
        self.remainingStates = State.remainingStates

    @chronom.chronomethod
    def saveTo(self,f):
        """ Use pickle to save important data in f """
        ff = open(f,"wb")
        pickle.dump(self,ff)
        ff.close()

    @staticmethod
    @chronom.chronomethod
    def fromFile(f):
        """ Use pickle to restore important data from f """
        ff = open(f,"rb")
        ret = pickle.load(ff)
        ff.close()
        return ret

    @chronom.chronomethod
    def apply(self, d = None):
        """ Restore the state tree, etc... from deserialized attributes """
        global device
        if d is not None:
            device = d

        State.states = self.states
        State.root = self.root
        State.remainingStates = self.remainingStates

@chronom.chronomethod
def init( d = None ):
    """ Init the state and set the global device """
    global device
    if d is not None:
        device = d
    State.init()
init()

@chronom.chronomethod
def loadContext( f ):
    """ Restores the context from a "context" file """
    Context.fromFile(f).apply()

def printAutomaton():
    """ Debug : show states and their transitions """
    print(" ----- Automaton ----- ")
    for si in State.remainingStates:
        print( "State " + str(si) + " :" )
        s = State.states[si]
        for t in s.transitions:
            print( " - " + t.toDebugString() )
        print()
