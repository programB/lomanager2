import time

from . pysidecompat import QtCore  # pyright: ignore
import logging

log = logging.getLogger("lomanager2_logger")


class ProcedureWorker(QtCore.QThread):
    """Worker thread intended to run install procedure"""

    # Define custom signals
    result = QtCore.Signal(str)

    def __init__(self, function_to_run, *args, **kwargs):
        super().__init__()

        self.function_to_run = function_to_run
        self.args = args
        self.kwargs = kwargs

    @QtCore.Slot()
    def run(self):
        """Run code inside in a separate thread"""

        log.debug(f"{self.function_to_run.__name__} function started in a new thread.")
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
            # with args/kwargs.
            self.output = self.function_to_run(*self.args, **self.kwargs)
            self.result.emit(self.output)
            return self.output

    def stop(self):
        self.is_running = False