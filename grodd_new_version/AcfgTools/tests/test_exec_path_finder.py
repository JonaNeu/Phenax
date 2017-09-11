import os
import unittest

from acfg_tools.exec_path_finder.acfg import AppGraph
# from acfg_tools.exec_path_finder.main import get_path_infos_for_alert
from acfg_tools.exec_path_finder.targets import generate_target_list


TEST_DOT = os.path.join(
    os.path.dirname(__file__), "test_files", "io.shgck.miniapp.dot"
)
TEST_INSTR = { "key": 91915601, "id": "5" }

TEST_TARGETS = os.path.join(
    os.path.dirname(__file__), "test_files", "targets.json"
)


class Tests(unittest.TestCase):

    def setUp(self):
        self.graph = AppGraph()
        self.graph.load_dot(TEST_DOT)

        self.targets = generate_target_list(TEST_TARGETS)

    def test_test_graph_has_alert(self):
        self.assertTrue(len(self.targets) > 0)
        self.assertTrue(len(self.targets[0].alerts) > 0)

    # def test_get_path_infos_for_alert(self):
    #     first_alert = self.targets[0].alerts[0]

    #     path_infos = get_path_infos_for_alert(self.graph, first_alert)
    #     self.assertNotEquals(path_infos, None)


if __name__ == '__main__':
    unittest.main()
