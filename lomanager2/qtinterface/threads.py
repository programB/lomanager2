"""
Copyright (C) 2023 programB

This file is part of lomanager2.

lomanager2 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3
as published by the Free Software Foundation.

lomanager2 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with lomanager2.  If not, see <http://www.gnu.org/licenses/>.
"""
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
