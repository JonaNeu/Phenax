import unittest

from acfg_tools.exec_path_finder.acfg import AppGraph
from test_exec_path_finder import TEST_DOT, TEST_INSTR


class AppGraphTests(unittest.TestCase):

    def setUp(self):
        self.invalid_graph = AppGraph()
        self.invalid_graph.load_dot("inexistant")
        self.valid_graph = AppGraph()
        self.valid_graph.load_dot(TEST_DOT)

    def test_load_dot(self):
        self.assertFalse(self.invalid_graph.is_valid)
        self.assertTrue(self.valid_graph.is_valid)

    def test_locate_instruction(self):
        node_id = self.valid_graph.locate_instruction(TEST_INSTR["key"])
        self.assertEquals(node_id, TEST_INSTR["id"])


if __name__ == '__main__':
    unittest.main()
