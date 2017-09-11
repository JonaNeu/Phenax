import unittest

# from acfg_tools.exec_path_finder.path_finder import PathFinder


class PathFinderTests(unittest.TestCase):
    """ Test PathFinder methods.

    Currently no tests available because I can't write DOT files on disk to
    produce a test sample.
    """

    # def test_get_soot_log(self):
    #     logs_and_results = [
    #         ("android.util.Log.i(\"JFL\", \"BEGINN7\")", "BEGINN7"),
    #         ("label1: android.util.Log.i(\"JFL\", \"BRANCHN6\")", "BRANCHN6"),
    #         ("android.util.Log.i(\"JFL\", \"BRANCHN43342\")", "BRANCHN43342")
    #     ]
    #     for log_and_result in logs_and_results:
    #         self.assertEquals(
    #             PathFinder.get_soot_log(log_and_result[0]),
    #             log_and_result[1]
    #         )


if __name__ == '__main__':
    unittest.main()
