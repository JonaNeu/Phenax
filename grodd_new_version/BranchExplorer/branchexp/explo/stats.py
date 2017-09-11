""" Compute stats on runs for future analysis and write JSON reports. """

import json
import logging

log = logging.getLogger("branchexp")

from branchexp.explo.tags import TagSet


class RunStats(object):
    """ Compute and write stats for a given run, with tag files.

    Attributes:
        stats: dict with tag lists and various useful information, see below.
        all_tags: TagSet for all tags (methods and conditions) added by ForceCFI
        seen_tags: TagSet for seen tags (methods and branches) seen during a run
    """

    def __init__(self, all_tags_file, seen_tags_file, run_id):
        self.run_id = run_id
        self.stats = {}
        self.all_tags = TagSet(all_tags_file)
        self.seen_tags = TagSet(seen_tags_file)

        self._gather_tags()

    def _gather_tags(self):
        """ Put all tags (seen and unseen) in a big "tags" dict. """
        self.stats["tags"] = {
            "all": {"method": self.all_tags.get_method_tags()
                    , "cond": self.all_tags.get_cond_tags()},
            "seen": {"method": self.seen_tags.get_method_tags()
                     , "branch": self.seen_tags.get_branch_tags()}
        }

    def find_partially_explored_cond(self):
        """ Compute the list of conditions partially explored,
        and fills the "partially_explored" dict """
        cond_partially_explored = {}

        for cond_tag in self.stats["tags"]["all"]["cond"]:
            left_branch, right_branch = cond_tag.split("/")

            # Branch fully explored
            if ( left_branch in self.stats["tags"]["seen"]["branch"]
                 and right_branch in self.stats["tags"]["seen"]["branch"] ):
                continue

            # Only explored left or right branch, add to our dict
            elif left_branch in self.stats["tags"]["seen"]["branch"]:
                cond_partially_explored[left_branch] = right_branch
            elif right_branch in self.stats["tags"]["seen"]["branch"]:
                cond_partially_explored[right_branch] = left_branch

            # Branching totally unexplored
            else:
                continue

        self.stats["partially_explored"] = cond_partially_explored

    def compute_global_stats(self, every_seen_tags):
        self.compute_coverage(every_seen_tags)

    def compute_coverage(self, every_seen_tags):
        """ Compute raw code coverage, taking into account previous runs """

        num_all_methods = len(self.stats["tags"]["all"]["method"])
        num_seen_methods = len(every_seen_tags["method"])
        num_all_branches = len(self.stats["tags"]["all"]["cond"]) * 2 + 1
        num_seen_branches = len(every_seen_tags["branch"]) + 1

        self.stats["coverage"] = {
            "method": (num_seen_methods / num_all_methods) * 100.0,
            "branch": (num_seen_branches / num_all_branches) * 100.0,
        }

    def analyse_targeted_execution(self, run_params, every_seen_tags):
        """ Compute coverage of monitored tags. """
        executed = []

        monitored_tags = run_params["monitor_tags"]

        for monitored in monitored_tags:
            if (monitored in every_seen_tags["method"]or
                    monitored in every_seen_tags["branch"]):
                executed.append(monitored)
                continue

        num_executed = len(executed)
        num_targeted = len(monitored_tags)
        if num_targeted > 0:
            coverage = (num_executed / num_targeted) * 100.0
        else:
            coverage = 0.0

        self.stats["targeted"] = {
            "target": run_params["target"],
            "alert": run_params["alert"],
            "executed": executed,
            "num_executed": num_executed,
            "num_targeted": num_targeted,
            "coverage": coverage
        }
        log.debug("Monitored tag(s):{}".format(monitored_tags))
        log.debug("Executed tag(s):{}".format(executed))
        return set(monitored_tags), set(executed)

    def log_digest(self):
        """ Log a succinct summary of the stats. """
        print("Results of run #{}:".format(self.run_id))

        num_seen_methods = len(self.stats["tags"]["seen"]["method"])
        num_all_methods = len(self.stats["tags"]["all"]["method"])
        print("- {}/{} method(s) have been executed.".format(
            num_seen_methods, num_all_methods
        ))

        num_seen_branches = len(self.stats["tags"]["seen"]["branch"])
        num_all_branches = len(self.stats["tags"]["all"]["cond"]) * 2
        print("- {}/{} conditional branch(es) have been explored.".format(
            num_seen_branches, num_all_branches
        ))
        print("- {}/{} targeted tag(s) have been executed.".format(
            self.stats["targeted"]["num_executed"],
            self.stats["targeted"]["num_targeted"]
        ))

        if "targeted" in self.stats:
            log.debug("Targeted instruction(s) have been hit: {:.2f}%"
                      .format(self.stats["targeted"]["coverage"]))
            log.debug("- Effectively executed: {}"
                      .format(self.stats["targeted"]["num_executed"]))
            log.debug("- Number of targeted instructions: {}".format(
                self.stats["targeted"]["num_targeted"]))

    def print_final(self):
        if "coverage" in self.stats:
            print("Final Results:")
            print("- Method coverage: {:.2f}%".format(
                self.stats["coverage"]["method"]
            ))
            print("- Branch coverage: {:.2f}%".format(
                self.stats["coverage"]["branch"]
            ))

    def write_json(self, json_filepath):
        """ Write a JSON file of these stats. """
        with open(json_filepath, "w") as json_file:
            json.dump( self.stats, json_file, cls=RunStatsJsonEncoder, indent=4)


class RunStatsJsonEncoder(json.JSONEncoder):
    """ Serialize to JSON more data types from our stats, like sets. """

    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        else:
            return json.JSONEncoder.default(self, obj)
