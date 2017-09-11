import logging
import subprocess

log = logging.getLogger("monkeyuiexrunner")

from branchexp.runners.base_runner import Runner
from branchexp.utils.utils import quit


class MonkeyUiExerciserRunner(Runner):
    """ Run the UI/Application Exerciser Monkey.

    Why not name it MonkeyRunner? Because it's exactly the name of a similar
    Google automatic tester project that we do not want to use.
    """

    def __init__(self, infos):
        super().__init__(infos)

    def run(self):
        self.prepare_run()

        monkey_command = [ "adb", "-s", self.device.name
                         , "shell", "monkey"
                         , "-p", self.package_name
                         , "-v", "500" ]

        log.info("Running the UI Exerciser Monkey")
        self.start_logcat()
        try:
            self.run_process = subprocess.Popen(monkey_command)
            self.run_process.wait()
        except OSError as exception:
            quit("An error occured during the automatic run: " + str(exception))
        self.stop_logcat()

        self.clean_after_run()


