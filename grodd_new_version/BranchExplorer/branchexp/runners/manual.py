import logging
import time

log = logging.getLogger("branchexp")

from branchexp.runners.base_runner import Runner


class ManualRunner(Runner):
    """ Simple manual runner.

    It just installs the application on the first device found and wait 10
    seconds for a human to do stuff.
    """

    def __init__(self, info):
        super().__init__(info)

    def run(self):
        self.prepare_run()

        log.info( "This is a manual run: the logcat controller will be running "
               +  "for 10 seconds only, meanwhile you can perform actions." )
        self.start_logcat()
        time.sleep(10)
        self.stop_logcat()

        self.clean_after_run()