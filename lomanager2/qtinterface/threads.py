import logging

from i18n import _

from .pysidecompat import *

log = logging.getLogger("lomanager2_logger")


class ProcedureWorker(QThread):
    """Worker thread intended to run install procedure"""

    result = Signal(str)

    def __init__(self, function_to_run, *args, **kwargs):
        super().__init__()

        self.function_to_run = function_to_run
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        """Run code inside in a separate thread"""

        log.debug(
            _("{} function started in a new thread.").format(
                self.function_to_run.__name__
            )
        )

        self.output = self.function_to_run(*self.args, **self.kwargs)
        self.result.emit(self.output)
        return self.output
