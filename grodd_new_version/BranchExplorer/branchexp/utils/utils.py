""" Utilities for BranchExplorer. """

import logging
import os
import sys

log = logging.getLogger("branchexp")


def quit(msg = None, code = 1):
    """ Exit function to clean stuff if necessary.
    code = 1 : Ctrl-c or other error
    code = 2 : Soot exited with error
    Use code 0 for a correct exit, 1 for a critical error (default).
    """
    if msg:
        if code == 1:
            log.critical(msg)
        else:
            log.info(msg)
    sys.exit(code)


def execute_in(directory):
    """ Decorator to change working directory to the given parameter during
    the execution of this method. """
    def function(func):
        def decorator(*args, **kwargs):
            current_dir = os.path.abspath(os.curdir)
            os.chdir(directory)
            return_value = func(*args, **kwargs)
            os.chdir(current_dir)
            return return_value
        return decorator
    return function
