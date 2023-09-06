import importlib.util
import logging

log = logging.getLogger("lomanager2_logger")

PySide6_spec = importlib.util.find_spec("PySide6")
PySide2_spec = importlib.util.find_spec("PySide2")

if PySide6_spec is not None:
    log.debug("Using PySide6")
    from PySide6 import QtCore, QtGui, QtWidgets
elif PySide2_spec is not None:
    log.debug("Using PySide2")
    from PySide2 import QtCore, QtGui, QtWidgets
else:
    log.debug("Neither PySide2 nor PySide6 Qt bindings where found")
