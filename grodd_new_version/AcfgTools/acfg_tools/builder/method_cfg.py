""" Wrapper for individual method CFGs with fancy methods and helpers. """

import os
import logging
import networkx as nx

from acfg_tools.builder.suspicious import add_risk_infos
from acfg_tools.builder.utils import SOOT_SIG, quit

log = logging.getLogger("branchexp")


ENTRY_POINT_SIGS = {
    # Activity's callbacks
    "activity_on_create_sig": (
        "onCreate",
        "void",
        "android.os.Bundle"
    ),
    "activity_on_start_sig": (
        "onStart",
        "void",
        ""
    ),
    "activity_on_resume_sig": (
        "onResume",
        "void",
        ""
    ),

    # Service's callbacks
    "service_on_start_command_sig": (
        "onStartCommand",
        "int",
        "android.content.Intent, int, int"
    ),
    "service_on_start_sig": (
        "onStart",
        "void",
        "android.content.Intent, int"
    ),
    "service_on_create_sig": (
        "onCreate",
        "void",
        ""
    ),
    # TODO: How to trigger onBind using adb?
    "service_on_Bind_sig": (
        "onBind",
        "android.os.IBinder",
        "android.content.Intent"
    ),

    # Receiver's callback(s)
    # TODO: How to trigger unregistered receiver?
    "receiver_on_receive_sig": (
        "onReceive",
        "void",
        "android.content.Context, android.content.Intent"
    )
}


class MethodCfg(object):
    """ CFG of a single method, can be loaded from a DOT file. """

    def __init__(self, dot_file = None):
        self.class_name = None
        self.name = None
        self.parameters = None
        self.return_type = None

        self.signature = None
        self.soot_signature = None
        self.has_title_node = False

        self.graph = None
        self.is_valid = False
        if dot_file:
            self.load_dot(dot_file)

    @property
    def full_name(self):
        return self.class_name + "." + self.name

    def __str__(self):
        return self.signature

    def load_dot(self, dot_file):
        """ Load a DOT file. """
        # print("Loading " + dot_file + "...")

        self.load_data_from_filename(dot_file)
        if self.name is None:
            return

        self.generate_signatures()
        self.load_graph(dot_file)
        if not self.is_graph_loaded():
            return

        self.add_title_node()
        self.strip_useless_attributes()

        # print("Graph for method " + self.signature + " loaded")
        self.is_valid = True

    def load_data_from_filename(self, filename):
        basename = os.path.basename(filename)
        match = SOOT_SIG.match(os.path.splitext(basename)[0])

        if not match:
            print(filename + " is a not a long filename")
            long_filename = self.get_long_filename(filename)
            if long_filename is not None:
                print(filename + " is a short filename for " + long_filename)
                basename = os.path.basename(long_filename)
                match = SOOT_SIG.match\
                    (os.path.splitext(basename)[0])
                if not match:
                    print("DOT filename unmatched by regex: " +
                          basename + ", ignored.")
                    return
            else:
                print("DOT filename unmatched by regex: " +
                      basename + ", ignored.")
                return

        info = match.groupdict()
        self.class_name = info["class"]
        self.name = info["method"]
        self.parameters = info["param"].split(",")
        self.return_type = info["type"]

    def get_long_filename(self, short_filename):
        short_names_file = short_filename[:short_filename.rfind('/')] +\
                           "/../short_file_names.txt"
        with open(short_names_file, "r") as f:
                for line in f:
                    if short_filename in line:
                        return line[line.find('\t') + 1:]
        return None

    def generate_signatures(self):
        self.signature = "{} {} ({})".format(
            self.return_type,
            self.full_name,
            ", ".join(self.parameters)
        )
        self.soot_signature = "<{}: {} {}({})>".format(
            self.class_name,
            self.return_type,
            self.name,
            ",".join(self.parameters)
        )

    def load_graph(self, dot_file):
        try:
            tmp = open(dot_file, "r")
            self.graph = nx.drawing.nx_agraph.read_dot(tmp)
            tmp.close()
        except Exception as e:
            print("An exception occurred during the loading of " + dot_file)
            print(e)

    def is_graph_loaded(self):
        return self.graph is not None and "name" in self.graph.graph

    def get_title_node(self):
        assert self.has_title_node
        return self.graph.graph[self.signature]

    def add_title_node(self):
        """ Add an ellipse node at the beginning of the method to mark its
        signature. """
        entry_nodes = self.get_entry_nodes()
        if len(entry_nodes) > 1:
            print("Warning: more than one entry node in this function")

        self.graph.add_node(
            self.signature, label=self.signature, shape="ellipse",
            soot_sig=self.soot_signature
        )
        if len(entry_nodes) == 0:
            print ("Warning: there is no entry point for this method")
            return
        entry_node = entry_nodes[0]
        self.graph.add_edge(self.signature, entry_node)
        self.has_title_node = True

    def get_entry_nodes(self):
        """ Get entry point nodes of the method (nodes without preds). """
        top_nodes = []
        for node in self.graph.nodes_iter():
            if len(self.graph.predecessors(node)) == 0:
                top_nodes.append(node)
        return top_nodes

    def strip_useless_attributes(self):
        """ Removes useless attributes left by Soot, like method labels. """
        graph_dict = self.graph.graph
        if "node" in graph_dict and "label" in graph_dict["node"]:
            graph_dict["node"].pop("label")
        if "graph" in graph_dict:
            graph_dict.pop("graph")

    def set_entry_point_attributes(self, is_main = False):
        entry_point = self.graph.node[self.signature]
        entry_point["entry_point"] = True
        entry_point["style"] = "filled"
        if is_main:
            entry_point["main"] = True
            entry_point["fillcolor"] = "green"
        else:
            entry_point["fillcolor"] = "greenyellow"

    def is_entry_point(self):
        for sig in ENTRY_POINT_SIGS.values():
            if (self.name == sig[0] and
                    self.return_type == sig[1] and
                    ", ".join(self.parameters) == sig[2]):
                return True
        return False

    def is_resource_dummy(self, package_name = None):
        if package_name is None:
            package_name = ""
        return (self.class_name.split("$")[0].endswith(package_name + ".R") and
                self.name == "<init>")

    def is_dummy_android_constructor(self, manifest):
        for activity in manifest.activities:
            if (self.class_name.split(".")[-1] == activity.short_name and
                    self.name == "<init>"):
                return True
        return False
