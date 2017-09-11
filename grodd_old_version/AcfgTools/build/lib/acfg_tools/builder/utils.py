""" Misc tools and utilities for ACFG builder. """

import re
import sys


SOOT_SIG = re.compile(
    r"<(?P<class>.+): "
    r"(?P<type>.+) "
    r"(?P<method>.+)\((?P<param>.*)\)>"
)


def quit(msg = None, code = 0):
    """ Proper exit function. """
    if msg:
        print(msg)
    sys.exit(code)


def separate_output(func):
    def decorator(*args, **kwargs):
        print((" " + func.__name__ + " ").center(80, "=") + "\n")
        return_value = func(*args, **kwargs)
        print("")
        return return_value
    return decorator
