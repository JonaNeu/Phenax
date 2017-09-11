import networkx as nx


class AppGraph(object):

    def __init__(self):
        self.graph = None
        self.is_valid = False

    def load_dot(self, dot_filepath):
        try:
            self.graph = nx.drawing.nx_agraph.read_dot(dot_filepath)
        except Exception as exception:
            print("An exception occurred during the loading of " + dot_filepath)
            print(exception)
            return
        self.is_valid = True

    def locate_instruction(self, key):
        """ Returns node_id of the corresponding instruction with key. """
        for node_id in self.graph.nodes_iter():
            node_key = self.graph.node[node_id].get("key", None)
            if node_key is None:
                continue
            if int(node_key) == key:
                return node_id

        raise GraphException("Couldn't locate instruction with key " + str(key))

    def get_node(self, node_id):
        return self.graph.node[node_id]

    def get_preds(self, node_id):
        return self.graph.predecessors(node_id)

    def get_successors(self, node_id):
        return self.graph.successors(node_id)


class GraphException(Exception):
    pass
