""" Full application control-flow graph """

import logging as log
import multiprocessing
import os

try:
    from progressbar import ProgressBar
    use_progressbar = True
except ImportError:
    use_progressbar = False

import networkx as nx

NUM_CORES = 8


class AppGraph(object):

    def __init__(self, manifest):
        self.graph = nx.MultiDiGraph()
        self.manifest = manifest
        self.main_activity = self.manifest.get_main_activity()

        self.ignored_packages = []

    def generate(self, cfgs, heuristics):
        self.load_ignored_packages(heuristics)

        method_cfgs = list(cfgs.values())
        self.multiproc_generate(method_cfgs)

        self.create_interproc_edges()
        self.graph.name = "Application graph"

    def load_ignored_packages(self, heuristics):
        self.ignored_packages = heuristics["packages_to_ignore"]

    def multiproc_generate(self, method_cfgs, processes = NUM_CORES):
        cfgs_sublists = []
        for i in range(processes):
            cfgs_sublists.append( method_cfgs[i::processes] )

        with multiprocessing.Pool(processes) as pool:
            graphs = pool.map(self.merge_cfgs, cfgs_sublists)

        for big_graph in graphs:
            self.graph = nx.disjoint_union(self.graph, big_graph)

    def merge_cfgs(self, method_cfgs):
        whole_graph = nx.MultiDiGraph()

        method_cfgs_iter = method_cfgs
        if use_progressbar:
            progress_bar = ProgressBar()
            method_cfgs_iter = progress_bar(method_cfgs_iter)

        for method_cfg in method_cfgs_iter:

            if self.is_method_useless(method_cfg):
                # print("Ignoring " + method_cfg.signature)
                continue

            if method_cfg.is_entry_point():
                is_main = method_cfg.class_name == self.main_activity
                method_cfg.set_entry_point_attributes(is_main = is_main)

            # method_cfg.evaluate_risk(heuristics["categories"])

            whole_graph = nx.disjoint_union(whole_graph, method_cfg.graph)

        return whole_graph

    def is_method_useless(self, method):
        """ Returns whether it's safe or not to discard this method CFG
        in an app graph.

        We have to be careful to not discard stuff that may even remotely have
        some useful semantics. I think it's best to simply state what I consider
        to be useless for the app CFG :

        * R.java generated classes constructor
        * Android objects constructors (for which overriding is forbidden)
        * Some packages that are way too big to be useful (e.g. android.support)
        """
        for package_to_ignore in self.ignored_packages:
            if method.class_name.startswith(package_to_ignore):
                return True

        package_name = self.manifest.package_name
        if method.class_name.startswith(package_name):
            if method.is_resource_dummy(package_name):
                print(method.class_name + " is a ressource class.")
                return True
            if method.is_dummy_android_constructor(self.manifest):
                print(method.signature + " is a dummy Android ctor.")
                return True

        return False

    def create_interproc_edges(self):
        # Generate a map sig to title node
        title_nodes = self.get_title_nodes()
        for node_id in self.graph.nodes_iter():
            self.handle_explicit_edges(node_id, title_nodes)
            self.handle_implicit_edges(node_id, title_nodes)

    def handle_explicit_edges(self, node_id, title_nodes):
        node = self.graph.node[node_id]
        target_sig = node.get("invoke_target", "")
        if target_sig and target_sig in title_nodes:
            self.graph.add_edge(
                node_id, title_nodes[target_sig],
                interproc = True
            )

    def handle_implicit_edges(self, node_id, title_nodes):
        node = self.graph.node[node_id]
        implicit_targets = node.get("implicit_targets", "")
        if not implicit_targets:
            return

        implicit_targets = implicit_targets.split(", ")
        print("Implicit flow targets: " + str(implicit_targets))

        last_implemented_sources = [node_id]
        for target_id in range(len(implicit_targets)):
            implicit_target = implicit_targets[target_id]
            if implicit_target in title_nodes:
                implemented_target = title_nodes[implicit_target]

                for source in last_implemented_sources:
                    self.graph.add_edge(
                        source, implemented_target,
                        interproc = True, implicit = True,
                        style = "dashed"
                    )
                last_implemented_sources = \
                        self.get_tails_from_node(implemented_target)

    def get_title_nodes(self):
        title_nodes = {}
        for node_id in self.graph.nodes_iter():
            sig = self.graph.node[node_id].get("soot_sig", "")
            if sig:
                title_nodes[sig] = node_id
        return title_nodes

    def get_tails_from_node(self, head):
        # If head is the title node, get the real head node (only successor)
        if "soot_sig" in self.graph.node[head]:
            head = self.graph.successors(head)[0]

        method_id = self.graph.node[head]["method"]
        subgraph = nx.dfs_tree(self.graph, head)

        tails = []
        for node_id in subgraph.nodes_iter():
            node = self.graph.node[node_id]
            if node.get("method", "") != method_id:
                continue
            if node.get("fillcolor", "") == "lightgray":  # Soot convention
                tails.append(node_id)
        return tails

    def write_dot(self, path = None):
        """ Save the app graph as a DOT file at parameter path. """
        log.warning("nx.write_dot seems to be broken with PyGraphviz for 3.4.")
        if path is None:
            path = os.path.join("output", self.manifest.package_name + ".dot")
        nx.write_dot(self.graph, path)
