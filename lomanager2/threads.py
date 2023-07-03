import time

from PySide6.QtCore import QThread, Signal, Slot

from applogic import configuration


class InstallProcedureWorker(QThread):
    """Worker thread intended to run install procedure"""

    # Define some custom signals
    result = Signal(str)
    progress = Signal(int)

    def __init__(self, function_to_run, *args, **kwargs):
        super().__init__()

        # Keep the reference to the arguments
        self.function_to_run = function_to_run
        self.args = args
        self.kwargs = kwargs

        # Add the reference to the emit method of the progress signal
        # to the kwargs dictionary
        # (but name in such a way it is immediately obvious what it does)
        # In the function_to_run this can be then used like so:
        # kwargs["inform_about_progress"](integer_value_here)
        # Note that function_to_run doesn't need to know
        # anything about Qt at all.
        self.kwargs["inform_about_progress"] = self.progress.emit

    @Slot()
    def run(self):
        """Run code inside in a separate thread"""

        # TODO: remove when not needed
        configuration.logging.warning("WIP, experimental code !")

        configuration.logging.info("Install procedure started in a new thread.")
        self.is_running = True

        # TODO: Remove the while loop?
        # This while loop shouldn't be needed as install procedure is just
        # doing its job and finishing, there is no need to wait in the thread
        # for any new portions of external data to pass it down to this procedure
        # Keeping it for now though just in case
        while True:
            if not self.is_running:  # When this flag becomes = False ...
                return  # ... exit thread.

            # TODO: It will be a good time to test if this solution is needed
            #       when the proper install procedure is in place.
            # Just in case the while loop runs so fast it doesn't release GIL
            time.sleep(0)

            # Take the function passed to the constructor and call(run) it,
            # with args/kwargs (extended with emit method of progress signal).
            self.output = self.function_to_run(*self.args, **self.kwargs)
            self.result.emit(self.output)
            return self.output

    def stop(self):
        self.is_running = False