import logging as log
import re


SOOT_LOGTAG = r"JFL"
SOOT_LOG = re.compile(
    r"(label\d+: )?android\.util\.Log\.i\(\"" +
    SOOT_LOGTAG +
    r"\", \"(?P<message>\w+)\"\)"
)


class PathFinder(object):

    def __init__(self, app_graph):
        self.graph = app_graph
        self.already_seen_node = []

    def process_alert(self, alert):
        path_infos = {}

        instr_node_id = self.graph.locate_instruction(alert.key)
        path_infos["nearest_tag"] = self.traceback_to_nearest_tag(instr_node_id)
        path_infos["entry_point"], path_infos["branches"] = \
            self.traceback_to_entry(instr_node_id)

        return path_infos

    def traceback_to_nearest_tag(self, node_id):
        tag = None

        current_id = node_id
        while True:
            preds = self.graph.get_preds(current_id)
            if len(preds) == 0:
                log.info("No more predecessors.")
                break

            pred_id = preds[0]
            pred_node = self.graph.get_node(pred_id)

            soot_log = PathFinder.get_soot_log(pred_node["label"])
            if soot_log is not None:
                tag = soot_log
                break

            current_id = pred_id

        if tag is None:
            log.error("Couldn't find nearest tag for node " + str(node_id))

        return tag

    def traceback_to_entry(self, node_id):
        """ Returns an entry_point (or None) and a list of branches to use and
        force to reach the instruction identified by node_id. """
        entry_point = None
        branches = []

        current_id = node_id
        while True:
            preds = self.graph.get_preds(current_id)
            if len(preds) == 0:
                log.info("No more predecessors.")
                break

            pred_id = preds[0]
            if pred_id in self.already_seen_node:
                log.warning( "Already seen that node ID: " + str(pred_id) + ", "
                             "stop looping." )
                break
            if len(preds) > 1:
                log.warning( "Multiple predecessors recursive exploration "
                             "is NOT implemented yet!" )
                self.already_seen_node.append(pred_id)

            pred_node = self.graph.get_node(pred_id)

            soot_log = PathFinder.get_soot_log(pred_node["label"])
            if soot_log and soot_log.startswith("BRANCH"):
                branches.append(soot_log)

            if pred_node.get("entry_point", None):
                entry_point = pred_node["soot_sig"]
                break
            else:
                current_id = pred_id

        return entry_point, branches

    @staticmethod
    def get_soot_log(label):
        match = SOOT_LOG.match(label)
        if match:
            return match.group("message")
        else:
            return None
