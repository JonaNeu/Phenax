#from acfg_tools.exec_path_finder.path_finder import PathFinder
import re

SOOT_LOGTAG = r"JFL"
SOOT_LOG = re.compile(
    r"(label\d+: )?android\.util\.Log\.i\(\"" +
    SOOT_LOGTAG +
    r"\", \"(?P<message>\w+)\"\)"
)


class Path(object):
    def __init__(self, graph=None, stmt_list=None):
        if graph is not None and stmt_list is not None:
            self.graph = graph
            self.statements = stmt_list  # contains list of node ids in graph
            self.signatures = []
            self.branches = []
            self.reduced = []
            self.__calculate_path_info()

    def add_pred(self, stmt):
        # stmt is e node id in the graph
        self.statements.insert(0, stmt)
        node = self.graph.get_node(stmt)
        soot_log = Path.get_soot_log(node["label"])
        if soot_log and soot_log.startswith("BRANCH"):
            self.branches.insert(0, soot_log)
            self.reduced.insert(0, False)
        if "soot_sig" in node:
            sig = node["soot_sig"]
            self.signatures.insert(0, sig)

    def __calculate_path_info(self):
        if self.signatures or self.branches or self.reduced:
            # Information has been calculated for this path
            print("Information already calculated for this path")
            return
        for stmt in self.statements:
            node = self.graph.get_node(stmt)
            soot_log = Path.get_soot_log(node["label"])
            if soot_log and soot_log.startswith("BRANCH"):
                self.branches.insert(0, soot_log)
                self.reduced.insert(0, False)
            if "soot_sig" in node:
                sig = node["soot_sig"]
                self.signatures.insert(0, sig)

    def copy(self):
        copy_path = Path()
        copy_path.graph = self.graph
        copy_path.statements = list(self.statements)
        copy_path.signatures = list(self.signatures)
        copy_path.branches = list(self.branches)
        copy_path.reduced = list(self.reduced)
        return copy_path

    def print_me(self):
        print("Statements: {}".format(self.statements))
        #print("Signatures: {}".format(self.signatures))
        print("Branches: {}".format(self.branches))
        print("Reduced: {}".format(self.reduced))

    def nbr_non_reduced(self):
        length = 0
        for i in range(len(self.branches)):
            if not self.reduced[i]:
                length += 1
        return length

    @staticmethod
    def get_soot_log(label):
        match = SOOT_LOG.match(label)
        if match:
            return match.group("message")
        else:
            return None
