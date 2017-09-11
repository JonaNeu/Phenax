import unittest

from acfg_tools.exec_path_finder.targets import generate_target_list
from test_exec_path_finder import TEST_TARGETS


class TargetsTests(unittest.TestCase):

    def setUp(self):
        self.target_list = generate_target_list(TEST_TARGETS)

    def test_generate_target_list(self):
        self.assertEquals(len(self.target_list), 1)

    def test_target_attributes(self):
        target = self.target_list[0]
        self.assertTrue(target.method_name != "")
        self.assertTrue(target.score != "")
        self.assertTrue(target.alerts != "")

    def test_alerts(self):
        target = self.target_list[0]
        alert = target.alerts[0]
        self.assertTrue(alert.category != "")
        self.assertTrue(alert.instruction != "")
        self.assertTrue(alert.key > 0)


if __name__ == '__main__':
    unittest.main()
