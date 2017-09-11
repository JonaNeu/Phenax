""" Full application control-flow graph """

import logging as log
import multiprocessing
import os
import logging
import time
import networkx as nx
import sys
from collections import defaultdict
from tempfile import mkstemp
from shutil import move
from os import remove, close

try:
    from progressbar import ProgressBar

    use_progressbar = True
except ImportError:
    use_progressbar = False

NUM_CORES = len(os.sched_getaffinity(0))
log = logging.getLogger("branchexp")


class ImpEdge(object):
    called_in_list = None
    caller = ''
    callee = ''
    rule_index = -1


class Rule(object):
    nbr = 0
    caller = ''
    callee = ''
    pos = 0
    freq = 0


class AppGraph(object):
    def __init__(self, manifest, doImplicit, exhaustive_paths, output_dir,
                 suspKeys, paths_out):
        self.graph = nx.MultiDiGraph()
        self.manifest = manifest
        self.main_activity = self.manifest.get_main_activity()

        self.ignored_packages = []
        self.all_sup = defaultdict(list)
        self.nbr_add_imp_edges = 0
        self.nbr_add_exp_edges = 0
        self.test = 0
        self.imp_edges_list = defaultdict(list)
        self.imp_edges_struct = list()
        self.rules = []
        self.doImplicit = doImplicit
        self.exhaustive_paths = exhaustive_paths
        self.output_dir = output_dir
        self.suspKeys = suspKeys
        self.imp_edges_file = "{}/genImpEdges.txt".format(self.output_dir)
        self.sup_file = "{}/allSup.txt".format(self.output_dir)
        self.first_imp_edge = True
        self.title_nodes = {}
        self.already_seen_node = []
        self.paths_out = paths_out

    def generate(self, cfgs, heuristics):
        self.load_ignored_packages(heuristics)

        method_cfgs = list(cfgs.values())

        self.multiproc_generate(method_cfgs)

        self.create_interproc_edges()
        self.graph.name = "Application graph"

        self.write_dot("{}/global.dot".format(self.output_dir))

        nbr_methods = self.count_methods()
        with open(self.paths_out, "a") as ff:
            ff.write("CFG info: methods: {}, nodes: {}, edges: {}\n"
                     .format(nbr_methods,
                             self.graph.number_of_nodes(),
                             self.graph.number_of_edges()))
        log.debug("CFG info: methods: {}, nodes: {}, edges: {}"
                  .format(nbr_methods,
                          self.graph.number_of_nodes(),
                          self.graph.number_of_edges()))

        with open("{}/edge_nbr.txt".format(self.output_dir), "a") as f:
            f.write("imp: {}\n".format(self.nbr_add_imp_edges))
            f.write("exp: {}\n".format(self.nbr_add_exp_edges))
            f.write("all: {}\n".format(self.nbr_add_imp_edges +
                                       self.nbr_add_exp_edges))

    def count_methods(self):
        nbr_methods = 0
        for n, d in self.graph.nodes(data=True):
            if "soot_sig" in d:
                nbr_methods += 1
        return nbr_methods

    def load_ignored_packages(self, heuristics):
        self.ignored_packages = heuristics["packages_to_ignore"]

    def multiproc_generate(self, method_cfgs, processes=NUM_CORES):
        print("Merging method CFGs on {} core(s)".format(processes))
        sys.stdout.flush()
        cfgs_sublists = []
        for i in range(processes):
            cfgs_sublists.append(method_cfgs[i::processes])

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
                method_cfg.set_entry_point_attributes(is_main=is_main)

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
                # print(method.class_name + " is a resource class.")
                return True
            if method.is_dummy_android_constructor(self.manifest):
                # print(method.signature + " is a dummy Android ctor.")
                return True

        return False

    def create_interproc_edges(self):
        start_time = time.time()
        print("Adding interprocedural edges")
        # Generate a map sig to title node
        self.get_title_nodes()

        if self.doImplicit:
            self.load_imp_edges()
            self.load_sup()

        for node_id in self.graph.nodes_iter():
            node = self.graph.node[node_id]
            sig_invoke = node.get("invoke_target", "")
            if sig_invoke:
                self.handle_explicit_edges(node_id, sig_invoke)
                sig_real = node.get("invoke_real", "")
                if sig_real and self.doImplicit:
                    self.handle_implicit_edges(node_id, sig_real)
        if self.exhaustive_paths and self.rules:
            with open(self.paths_out, "a") as f:
                f.write("Rules:\n")
                for rule in self.rules:
                    if rule.freq != 0:
                        f.write(" * {}#{}#{}#{}\n".
                                format(rule.freq,
                                       rule.caller,
                                       rule.callee,
                                       rule.pos))
        else:
            log.debug("exhaustive_paths not correct: {}".
                      format(self.exhaustive_paths))
            log.debug("rules not correct: {}".
                      format(self.rules))

        print("Explicit edge(s): {0}".format(self.nbr_add_exp_edges))
        print("Implicit edge(s): {0}".format(self.nbr_add_imp_edges))

        time_diff = time.time() - start_time
        with open("{}/calc_time.txt".format(self.output_dir), "a") as f:
            f.write("Building global CFG took: {} secs\n".
                    format(time_diff))
        log.debug("Building global CFG took: {} secs".format(time_diff))

    def load_imp_edges(self):
        n_loaded_imp_edges = 0
        nbr_lines = 0
        with open(self.imp_edges_file) as f:
            rules = True
            for line in f:
                line = line.rstrip()
                if line == "Rules:":
                    rules = True
                    continue
                elif line == "Implicit edges:":
                    rules = False
                    log.debug("{} rule(s) loaded".
                              format(len(self.rules)))
                    continue
                if rules:
                    # Format:
                    # rule_number#caller#callee#position
                    l = line.split('#')
                    if l and len(l) == 4:
                        rule = Rule()
                        rule.nbr = int(l[0])
                        rule.caller = str("<" + l[1] + ">")
                        rule.callee = str("<" + l[2] + ">")
                        rule.pos = int(l[3])
                        self.rules.append(rule)
                    else:
                        log.error('Error: {0} of unknown format, line: {1}'
                                  .format(self.imp_edges_file, line))
                        sys.exit(-1)
                else:
                    # Format:
                    # rule_number { <called_in> @ <called_in> ... } ->
                    #   caller -> callee
                    nbr_lines += 1
                    l = line.split(' -> ')
                    if l and len(l) == 3:
                        self.imp_edges_list[str("<" + l[1] + ">")]\
                            .append(str("<" + l[2] + ">"))
                        n_loaded_imp_edges += 1
                        imp_edge = ImpEdge()
                        imp_edge.caller = str("<" + l[1] + ">")
                        imp_edge.callee = str("<" + l[2] + ">")
                        imp_edge.rule_index = int(l[0][0:l[0].find('{') - 1])
                        imp_edge.called_in_list = list()
                        l[0] = l[0][l[0].find('{') + 2:-2]
                        l2 = l[0].split(' @ ')
                        for called_in in l2:
                            imp_edge.called_in_list.append(called_in)
                        self.imp_edges_struct.append(imp_edge)
                    else:
                        log.error('Error: {0} of unknown format, line: {1}'
                                  .format(self.imp_edges_file, line))
                        sys.exit(-1)
        log.debug("Loaded implicit edges: {0}".
                  format(n_loaded_imp_edges))

    def load_sup(self):
        n_sup = 0
        with open(self.sup_file) as f:
            for line in f:
                line = line.rstrip()
                l = line.split(' ')
                for i in range(len(l)):
                    self.all_sup[str(l[0])].append(str(l[i]))
                n_sup += 1

    def handle_explicit_edges(self, node_id, sig_invoke):
        if sig_invoke in self.title_nodes:
            self.graph.add_edge(
                node_id, self.title_nodes[sig_invoke],
                interproc=True
            )
            self.nbr_add_exp_edges += 1

    def handle_implicit_edges(self, node_id, sig_real):
        if sig_real in self.imp_edges_list:
            for callee in self.imp_edges_list[sig_real]:
                if callee in self.title_nodes \
                        and not self.super_call_incorrect(node_id, sig_real,
                                                          callee):
                    self.graph.add_edge(node_id,
                                        self.title_nodes[callee],
                                        interproc=True, implicit=True,
                                        style="dashed", color="green")
                    self.nbr_add_imp_edges += 1
                    if self.exhaustive_paths:
                        for impEdge in self.imp_edges_struct:
                            if impEdge.caller == sig_real \
                                 and impEdge.callee == callee:
                                with open(self.paths_out, "a") as f:
                                    if self.first_imp_edge:
                                        self.first_imp_edge = False
                                        f.write("Implicit edges:\n")
                                    f.write(" + { ")
                                    first = True
                                    for called_in in \
                                            impEdge.called_in_list:
                                        if first:
                                            first = False
                                        else:
                                            f.write(" @ ")
                                        f.write(called_in)
                                    f.write(" }} -> {} -> {}\n".format(sig_real,
                                                                       callee))
                                self.rules[impEdge.rule_index].freq += 1
                                break

    def super_call_incorrect(self, node_id, sig_real, callee):
        # Check just for <init> functions (constructors)
        if "<init>" not in sig_real:
            return False

        rule = Rule()
        for e in self.imp_edges_struct:
            if e.caller == sig_real and e.callee == callee:
                rule = self.rules[e.rule_index]
                break
        if rule.pos != 0:
            return False

        self.already_seen_node = []
        called_in = self.called_in(node_id)
        if not called_in:
            log.error("No called_in for node " + self.graph.node[node_id])
            exit()

        # Allow only calls from init
        if "init" not in called_in:
            return True

        called_in_class = called_in[1:called_in.find(":")]
        caller_class = rule.caller[1:rule.caller.find(":")]
        callee_class = callee[1:callee.find(":")]
        if caller_class in self.all_sup[callee_class] and\
            caller_class in self.all_sup[called_in_class] and\
                called_in_class != callee_class:
            return True
        else:
            return False

    def called_in(self, node_id):
        preds = self.graph.predecessors(node_id)
        if len(preds) == 0:
            return None

        for i in range(len(preds)):
            pred_id = preds[i]
            if pred_id in self.already_seen_node:
                continue

            self.already_seen_node.append(pred_id)
            pred_node = self.graph.node[pred_id]
            if "soot_sig" in pred_node:
                return pred_node["soot_sig"]
            else:
                pred_called_in = self.called_in(pred_id)
                if pred_called_in:
                    return pred_called_in

        return None

    def get_title_nodes(self):
        for node_id in self.graph.nodes_iter():
            sig = self.graph.node[node_id].get("soot_sig", "")
            if sig:
                self.title_nodes[sig] = node_id

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

    def write_dot(self, path=None):
        """ Save the app graph as a DOT file at parameter path. """
        log.warning("nx.write_dot seems to be broken with PyGraphviz for 3.4.")
        if path is None:
            path = os.path.join("output", self.manifest.package_name + ".dot")
        nx.drawing.nx_agraph.write_dot(self.graph, path)
        self.color_suspicious(path)

    def color_suspicious(self, path):
        fh, abs_path = mkstemp()
        with open(abs_path, 'w') as new_file:
            with open(path) as old_file:
                for line in old_file:
                    for key in self.suspKeys:
                        if key in line:
                            line += "fillcolor=yellow,style=filled,\n"
                            line += "suspicious_instruction=true,\n"
                            break
                    new_file.write(line)
        close(fh)
        remove(path)
        move(abs_path, path)
