import gettext
import logging
import time

from .pysidecompat import QtCore  # pyright: ignore

t = gettext.translation("lomanager2", localedir="./locales", fallback=True)
_ = t.gettext
log = logging.getLogger("lomanager2_logger")


class ProcedureWorker(QtCore.QThread):
    """Worker thread intended to run install procedure"""

    result = QtCore.Signal(str)

    def __init__(self, function_to_run, *args, **kwargs):
        super().__init__()

        self.function_to_run = function_to_run
        self.args = args
        self.kwargs = kwargs

    @QtCore.Slot()
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
