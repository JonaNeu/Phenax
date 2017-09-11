import logging

log = logging.getLogger("branchexp")

from acfg_tools.exec_path_finder.targets import generate_target_list


class TargetSelector(object):
    """ Parse a target JSON file and decide what are interesting targets
    to focus on. """

    def __init__(self, targets_file=None):
        self.targets = None

        if targets_file:
            self.load_targets(targets_file)

    def load_targets(self, targets_file):
        self.targets = generate_target_list(targets_file)
        print("Found {} suspicious method(s)".format(len(self.targets)))
        if self.targets:
            print("Found {} suspicious method(s)".format(len(self.targets)))
            log.debug("All targets:")
            for target in self.targets:
                log.debug("- " + str(target))

    def get_selected_targets(self, max_targets):
        """ Return at most max_targets targets from the loaded target file. """
        if not self.targets:
            return self.targets

        target_score_key = lambda target: target.score
        sorted_targets = sorted(self.targets
                                , key=target_score_key
                                , reverse=True)
        selected_targets = sorted_targets[:max_targets]

        print("Selected targets to trigger:")
        for target in selected_targets:
            print("- " + str(target))

        return selected_targets

    def get_all_targets(self):
        """ Return at most max_targets targets from the loaded target file. """
        if not self.targets:
            return self.targets

        target_score_key = lambda target: target.score
        all_targets = sorted(self.targets
                                , key=target_score_key
                                , reverse=True)
        return all_targets
