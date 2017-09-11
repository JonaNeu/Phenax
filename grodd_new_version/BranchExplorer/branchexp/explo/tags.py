""" Functions to work with tags and tag files. """

import logging

log = logging.getLogger("branchexp")


def is_method_tag(tag):
    return tag.startswith("BEG")

def is_branch_tag(tag):
    return tag.startswith("BRA") and not "/" in tag

def is_cond_tag(tag):
    return tag.startswith("BRA") and "/" in tag


class TagSet(object):
    """ Container for tags, as used by ForceCFI.

    A TagSet can contain different types of tags, depending on who computed it:

    * method tags, which look like "BEGINN1"
    * branch tags, which look like "BRANCHN2"
    * cond tags, which look like "BRANCHN3/BRANCHN4"

    Method tags can be written by ForceCFI or during the logcat monitoring.
    Branches alone are usually only written by logcat or when we compute a set
    of branches to force. Cond tags are written exclusively by ForceCFI, to keep
    paired together two branches of a same conditional jump. I'm not sure if
    it's useful right now but it may be in the future. Beware of not mixing them
    with branch tags though!

    Attributes:
        tags: set of tags (strings)
    """

    def __init__(self, tag_filepath = None):
        self.reset()
        if tag_filepath is not None:
            self.load_file(tag_filepath)

    def reset(self):
        self.tags = set()

    def load_file(self, tag_filepath):
        self.reset()
        with open(tag_filepath, "r") as tag_file:
            for line in tag_file.readlines():
                self.tags.add(line.strip("\n"))

    def write_file(self, tag_filepath):
        with open(tag_filepath, "w") as tag_file:
            for tag in self.tags:
                tag_file.write(tag + "\n")

    def get_method_tags(self):
        return set([tag for tag in self.tags if is_method_tag(tag)])

    def get_branch_tags(self):
        return set([tag for tag in self.tags if is_branch_tag(tag)])

    def get_cond_tags(self):
        return set([tag for tag in self.tags if is_cond_tag(tag)])

    def split_cond_in_branches(self, cond):
        """ Removes a cond BRANCH1/BRANCH2 from the tags
        and adds BRANCH1 and BRANCH2. """
        if cond in self.tags:
            left_branch, right_branch = cond.split("/")
            self.tags.remove(cond)
            self.tags.add(left_branch)
            self.tags.add(right_branch)
