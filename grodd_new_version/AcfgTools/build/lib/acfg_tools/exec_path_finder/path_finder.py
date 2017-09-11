import logging
from acfg_tools.exec_path_finder.path import Path

log = logging.getLogger("branchexp")


class PathFinder(object):

    def __init__(self, app_graph, exhaustive_paths, paths_out):
        self.graph = app_graph
        self.already_seen_node = []
        self.paths = []
        self.entry_point = None
        self.exhaustive_paths = exhaustive_paths
        self.paths_out = paths_out

    def process_alert(self, alert, alert_types):
        log.debug("Processing alert: {}".format(alert.key))
        path_info = {}

        instr_node_id = self.graph.locate_instruction(alert.key)
        path_info["nearest_tag"] = \
            self.traceback_to_nearest_tag(instr_node_id)
        path_info["entry_point"], path_info["branches"] = \
            self.traceback_to_entry(instr_node_id, alert_types)

        return path_info

    def traceback_to_nearest_tag(self, node_id):
        tag = None
        already_seen = []
        current_ids = [node_id]

        while True:
            if not current_ids:
                # print("Exit SIZE: {}".format(len(current_ids)))
                break
            # print("current_ids: {}".format(current_ids))
            brk = False
            new_ids = []
            for i in current_ids:
                preds = self.graph.get_preds(i)
                if len(preds) == 0:
                    # log.debug("No more predecessors.")
                    continue
                for pred_id in preds:
                    if pred_id in already_seen:
                        continue
                    already_seen.append(pred_id)

                    pred_node = self.graph.get_node(pred_id)
                    soot_log = Path.get_soot_log(pred_node["label"])
                    if soot_log is not None:
                        tag = soot_log
                        # print("Tag found: {}".format(tag))
                        brk = True
                        break
                    else:
                        new_ids.append(pred_id)
            current_ids[:] = new_ids
            if brk:
                break

        if tag is None:
            log.error("Couldn't find nearest tag for node {}: {}"
                      .format(node_id, self.graph.get_node(node_id)))

        return tag

    def traceback_to_entry(self, node_id, alert_types):
        """ Returns an entry_point (or None) and a list of branches to use and
        force to reach the instruction identified by node_id. """
        self.entry_point = None
        # self.branches = []

        suspect_id = node_id
        if self.exhaustive_paths:
            self.get_paths(suspect_id)
        else:
            path_statements = self.get_preds(suspect_id)
            if path_statements:
                self.paths.append(Path(path_statements))

        # Get the list of branches that are in the path to force
        # for p in self.paths:
        #     self.__calculate_path_info(p)

        # TODO: Remove or comment this bloc
        # print("Paths BEFORE reduction: ")
        # self.log_path_info()

        # Keep only paths with smallest number of branches among similar ones
        self.__reduce_paths(self.paths)

        # print("Paths AFTER reduction: ")
        self.log_path_info(alert_types)

        # return branches of the shortest path -- path with less branches
        branches = []
        for i in range(len(self.paths)):
            if i == 0:
                branches = self.paths[i].branches
                continue
            if len(branches) < len(self.paths[i].branches):
                branches = self.paths[i].branches
        return self.entry_point, branches

    def __reduce_paths(self, paths, posterior=True):
        # if there is 0 or 1 path, nothing to reduce
        if not paths or len(paths) <= 1:
            return
        #
        tmp_paths = []
        for i in range(len(paths)):
            if paths[i] is not None and \
                    self.__is_shorter_than_similar(paths, i, posterior):
                # print("Keep path {}".format(i))
                tmp_paths.append(paths[i])

        paths[:] = [p for p in tmp_paths]

        # Remove reduced branches
        self.__remove_reduced_branches(paths)

    @staticmethod
    def __remove_reduced_branches(paths):
        for path in paths:
            new_branches = []
            new_reduced = []
            for i in range(len(path.branches)):
                if not path.reduced[i]:
                    new_branches.append(path.branches[i])
                    new_reduced.append(False)
            path.branches = new_branches
            path.reduced = new_reduced

    def __is_shorter_than_similar(self, paths, path_index, posterior):
        i = path_index
        for j in range(i + 1, len(paths)):
            if paths[j] is not None:
                if not self.__similar_path(paths, i, j):
                    # Case 1: do not contain same method signatures
                    # -> do nothing
                    continue
                else:
                    # Remove the "else" branch tag
                    first = self.__reduce_else_tags(paths, i, j, posterior)
                    second = self.__reduce_else_tags(paths, j, i, posterior)
                    if first and second:
                        if paths[i].nbr_non_reduced() < \
                                paths[j].nbr_non_reduced():
                            # Case 2: i contains less branches than j
                            # -> j = None
                            paths[j] = None
                        elif paths[i].nbr_non_reduced() > \
                                paths[j].nbr_non_reduced():
                            # Case 3: j contains less branches than i
                            # -> i = None & return False
                            paths[i] = None
                            return False
                        # Same number of branches
                        elif posterior:
                            # keep i
                            paths[j] = None
                        else:
                            # print("Keep both")
                            pass

        # There is no better path than path_index
        return True

    # Returns True if heads are similar, and False if they are different
    def __reduce_else_tags(self, paths, i, j, posterior):
        # print("Path {}".format(i))
        # paths[i].print_me()
        # print("Path {}".format(j))
        # paths[j].print_me()

        # indexes of branches of paths i and j respectively
        x = 0
        y = 0

        while x < len(paths[i].branches) and \
                y < len(paths[j].branches):
            # Skip identical branches
            if paths[i].branches[x] ==\
                    paths[j].branches[y]:
                x += 1
                y += 1
                continue

            else:
                if not posterior:
                    if x == 0:
                        # print("Heads are different, no reduce: {} =!= {}"
                        #       .format(paths[i].branches[x],
                        #               paths[j].branches[y]))
                        return False
                # Have we reduced the difference?
                reduced = False

                for l in range(x, len(paths[i].branches)):
                    for m in range(y, len(paths[j].branches)):
                        if paths[i].branches[l] == \
                             paths[j].branches[m]:
                            # print("match {} = {}".format(
                            #      paths[i].branches[l],
                            #      paths[j].branches[m]))
                            # Mark branches from x to l on i as reduced
                            for z in range(x, l):
                                # print("Reduce a: {}".format(
                                #     paths[i].branches[z]))
                                paths[i].reduced[z] = True
                            # move x forward
                            x = l+1
                            # Remove branches from y to m on j
                            for t in range(y, m):
                                # print("Reduce b: {}".format(
                                #      paths[j].branches[t]))
                                paths[j].reduced[t] = True
                            # move y forward
                            y = m + 1
                            # Reduction done -> Break the 2 loops
                            reduced = True
                            break
                    if reduced:
                        break
                if not reduced:
                    # Cannot reduce the difference
                    # print("Cannot reduce the difference from {} and {}"
                    #       .format(paths[i].branches[x], paths[j].branches[y]))
                    return True
        return True

    # Paths cross the same methods signatures
    def __similar_path(self, paths, i, j):
        if paths[i] is None or paths[j] is None or \
                        len(paths[i].signatures) != \
                        len(paths[j].signatures):
            return False
        for k in range(len(paths[i].signatures)):
            if paths[i].signatures[k] != paths[j].signatures[k]:
                return False
        # print("Similar paths {} and {}".format(i, j))
        return True

    def log_path_info(self, alert_types):
        # Print some debug information about paths
        if not self.paths:
            log.debug("Path: 0 branch(es) - type(s) {}"
                      .format(alert_types))
        else:
            # We can have multiple paths for a given statement if
            # exhaustive_paths == 1
            for i in range(len(self.paths)):
                log.debug("Path: {} branch(es) {} - type(s) {}".
                          format(len(self.paths[i].branches),
                                 self.paths[i].branches, alert_types))
                for a_node_id in self.paths[i].statements:
                    a_node = self.graph.get_node(a_node_id)
                    if "soot_sig" in a_node:
                        sig = a_node["soot_sig"]
                        log.debug(" - {}".format(sig))

        # Write some information about paths in a file
        if self.exhaustive_paths:
            with open(self.paths_out, "a") as f:
                if not self.paths:
                    f.write("Path: 0 branch(es) - type(s) {}\n"
                            .format(alert_types))
                else:
                    for i in range(len(self.paths)):
                        f.write("Path: {} branch(es) {} - type(s) {}\n".
                                format(len(self.paths[i].branches),
                                       self.paths[i].branches, alert_types))
                        for a_node_id in self.paths[i].statements:
                            a_node = self.graph.get_node(a_node_id)
                            if "soot_sig" in a_node:
                                sig = a_node["soot_sig"]
                                sig = sig[1:len(sig) - 1]
                                f.write(" - {}\n".format(sig))

            # TODO: Remove or comment this bloc
            # Some extra details about paths (print path statement labels)
            # for i in range(len(self.paths)):
            #     log.debug("Path: {} branch(es) {}".
            #               format(len(self.paths[i].branches),
            #                      self.paths[i].branches))
            #     for node_id in self.paths[i].statements:
            #         a_node = self.graph.get_node(node_id)
            #         if "label" in a_node:
            #             label = a_node["label"]
            #             log.debug(" - {}".format(label))

    def get_preds(self, current_id):
        preds = self.graph.get_preds(current_id)
        if len(preds) == 0:
            # log.debug("No more predecessors.")
            return []
        for i in range(len(preds)):
            pred_id = preds[i]
            if pred_id in self.already_seen_node:
                #log.warning("Already seen that node ID: " + str(pred_id) + ", "
                #           "stop looping.")
                continue

            self.already_seen_node.append(pred_id)

            pred_node = self.graph.get_node(pred_id)
            if pred_node.get("entry_point", None):
                self.entry_point = pred_node["soot_sig"]
                return [current_id, pred_id]
            else:
                returned = self.get_preds(pred_id)
                if returned and self.entry_point is not None:
                    returned.append(current_id)
                    return returned
        return []

    # TODO: Split this function
    # Warning: The algorithm is exponential !!!
    def get_paths(self, suspect_id):
        tmp_paths = [Path(self.graph, [suspect_id])]
        # suspicious_meth_id = self.graph.get_preds(
        #     self.graph.get_preds(suspect_id)[0])[0]
        # suspicious_meth = self.graph.get_node(suspicious_meth_id)

        max_iter_without_reduce = 5  # 2^10 = 1024
        iter_without_reduce = 0
        iter_nbr = -1
        while True:
            iter_nbr += 1
            # Reduce the number of suffixes every n iterations
            if iter_without_reduce >= max_iter_without_reduce - 1:
                # print("Reducing inside get_paths, iter: {}".format(iter_nbr))
                self.__reduce_paths(tmp_paths, posterior=False)
                iter_without_reduce = 0
            iter_without_reduce += 1

            updated = False
            size = len(tmp_paths)
            # print("Nbr suffixes: {}".format(size))
            # Interrupt the method id it goes exponential
            if size >= 1000:
                log.debug("Calculation is going crazy, nbr of search paths: {}"
                          .format(size))
                return
            #
            # print("Suspicious tag: {}: {}".
            #       format(suspicious_meth_id, suspicious_meth))
            # print("suffixes List: \n{}"
            #       .format([p.statements for p in tmp_paths if p is not None]))
            # iter on the umber of suffixes
            for i in range(size):

                # Skip null suffixes, those already added to self.paths
                if tmp_paths[i] is None:
                    continue

                preds = self.graph.get_preds(tmp_paths[i].statements[0])
                if len(preds) == 0:
                    # No more predecessors, continue to the next tmp suffix
                    # print("No more preds")#, suffix: {}".format(tmp_paths[i]))
                    tmp_paths[i] = None
                    continue
                # print("Preds nbr: {}".format(len(preds)))

                # Number of predecessors seen before in this suffix
                nbr_seen = 0

                # First predecessor to take effectively
                first_pred = True

                # Make a copy of the current suffix, replace it by first pred
                current_path = tmp_paths[i].copy()

                # iter on the number of preds
                for j in range(len(preds)):
                    pred_id = preds[j]

                    # Skip predecessor if seen before (avoid looping)
                    if pred_id in current_path.statements:
                        nbr_seen += 1
                        # print("Seen id: {}, node: {}".
                        #       format(pred_id, self.graph.get_node(pred_id)))
                        # print("Current Suffix: {}"
                        #       .format(current_path.statements))
                        continue

                    pred_node = self.graph.get_node(pred_id)

                    # Do not cross @caughtexception
                    if pred_node["label"] and \
                            "@caughtexception" in pred_node["label"]:
                        nbr_seen += 1  # Not really seen, just to avoid looping
                        # print("Exception: {}, node: {}".
                        #       format(pred_id, self.graph.get_node(pred_id)))
                        # print("Current Suffix: {}"
                        #       .format(current_path.statements))
                        continue

                    # This is a valid predecessor
                    # print("Valid pred: {} of {}"
                    #       .format(pred_id, current_path.statements[0]))
                    updated = True

                    # Add the first valid predecessor to the original suffix
                    # and create new suffixes for the other predecessors
                    if first_pred:
                        new_suffix = tmp_paths[i]
                    else:
                        new_suffix = current_path.copy()
                    new_suffix.add_pred(pred_id)
                    if pred_node.get("entry_point", None):
                        # Set the first found entry point as the main one
                        if self.entry_point is None:
                            self.entry_point = pred_node["soot_sig"]
                        self.paths.append(new_suffix.copy())
                        # Set the suffix to None if it is the original one
                        if first_pred:
                            first_pred = False
                            tmp_paths[i] = None
                    else:
                        # Add the new suffix to tmp_paths if it is not the
                        # original one
                        if not first_pred:
                            tmp_paths.append(new_suffix.copy())

                    # We are here because we found a valid predecessor
                    if first_pred:
                        first_pred = False

                # Set suffix to None if all predecessors have been seen before
                if nbr_seen == len(preds):
                    # print("All preds seen, set suffix to None")
                    tmp_paths[i] = None

            # Exit while loop if no update
            if not updated:
                break
