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
import importlib.util
import logging

log = logging.getLogger("lomanager2_logger")

PySide6_spec = importlib.util.find_spec("PySide6")
PySide2_spec = importlib.util.find_spec("PySide2")

if PySide6_spec is not None:
    log.debug("Using PySide6")
    from PySide6.QtCore import *  # type: ignore
    from PySide6.QtGui import *  # type: ignore
    from PySide6.QtNetwork import QAbstractSocket  # type: ignore
    from PySide6.QtWidgets import *  # type: ignore
elif PySide2_spec is not None:
    log.debug("Using PySide2")
    from PySide2.QtCore import *  # type: ignore
    from PySide2.QtGui import *  # type: ignore
    from PySide2.QtNetwork import QAbstractSocket  # type: ignore
    from PySide2.QtWidgets import *  # type: ignore
else:
    log.debug("Neither PySide2 nor PySide6 Qt bindings where found")
