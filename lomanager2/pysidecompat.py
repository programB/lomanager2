import importlib.util
PySide6_spec = importlib.util.find_spec("PySide6")
PySide2_spec = importlib.util.find_spec("PySide2")

if PySide6_spec is not None:
    print("Using PySide6")
    from PySide6 import QtGui
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QTableView,
        QTextEdit,
        QVBoxLayout,
        QWidget,
        QHeaderView,
        QItemDelegate,
    )
    from PySide6.QtCore import (
        QObject,
        QAbstractItemModel,
        QAbstractTableModel,
        QSortFilterProxyModel,
        Qt,
        Signal,
        Slot,
        QThread,
        QModelIndex,
        QEvent,
    )
elif PySide2_spec is not None:
    print("Using PySide2")
    from PySide2 import QtGui
    from PySide2.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QTableView,
        QTextEdit,
        QVBoxLayout,
        QWidget,
        QHeaderView,
        QItemDelegate,
    )
    from PySide2.QtCore import (
        QObject,
        QAbstractItemModel,
        QAbstractTableModel,
        QSortFilterProxyModel,
        Qt,
        Signal,
        Slot,
        QThread,
        QModelIndex,
        QEvent,
    )
else:
    print("Neither PySide2 nor PySide6 Qt bindings where found")
