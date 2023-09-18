import importlib.util
import logging

log = logging.getLogger("lomanager2_logger")

PySide6_spec = importlib.util.find_spec("PySide6")
PySide2_spec = importlib.util.find_spec("PySide2")

if PySide6_spec is not None:
    log.debug("Using PySide6")
    from PySide6.QtCore import *  # type: ignore
    from PySide6.QtGui import *  # type: ignore
    from PySide6.QtWidgets import *  # type: ignore
    from PySide6.QtNetwork import QAbstractSocket  # type: ignore
elif PySide2_spec is not None:
    log.debug("Using PySide2")
    from PySide2.QtCore import *  # type: ignore
    from PySide2.QtGui import *  # type: ignore
    from PySide2.QtWidgets import *  # type: ignore
    from PySide2.QtNetwork import QAbstractSocket  # type: ignore
else:
    log.debug("Neither PySide2 nor PySide6 Qt bindings where found")
