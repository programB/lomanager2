import sys
from typing import Any

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableView,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from PySide6.QtCore import (
    QAbstractTableModel,
    Qt,
)


class PackageMenuModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()

        # TODO: Holding the data inside model
        #       for testing only.
        #       To be replaced by a proper
        #       data object.
        self.package_menu = [
            [
                "OpenOffice",
                "core-packages",
                "2.1",
                True,
                False,
                False,
            ],
            [
                "LibreOffice",
                "core-packages",
                "7.4",
                False,
                True,
                False,
            ],
        ]

    def data(self, index, role) -> Any:
        """Returns data item as requested by the View.

        Parameters
        ----------
        index : QModelIndex | QPeristentModelIndex
            Points to a specific data item in data model

        role : DisplayRole
           Each data item in data model may have many data elements
           associated with it. role, passed in by the View, indicates
           to the model which element of the data item is needed.


        Returns
        -------
        Any
            Data type depends on data and role
        """

        row = index.row()
        column = index.column()
        item = self.package_menu[row][column]

        if role == Qt.ItemDataRole.DisplayRole:
            return item

    def rowCount(self, index) -> int:
        """Tells how many rows of data there are.

        Parameters
        ----------
        index : QModelIndex | QPeristentModelIndex
            Points to a specific data item in data model

        Returns
        -------
        int
            Number of rows
        """

        return len(self.package_menu)

    def columnCount(self, index) -> int:
        """Tells how many columns of data there are.

        Parameters
        ----------
        index : QModelIndex | QPeristentModelIndex
            Points to a specific data item in data model

        Returns
        -------
        int
            Number of rows
        """

        # For the intended way of displaying package status
        # there will always be fixed number of 6 columns.
        return 6

    def headerData(self, section: int, orientation, role) -> str | None:
        """Returns descriptions for each column in the data.

        Parameters
        ----------
        orientation : Orientation
            Orientation of the header as requested by the View,
            either Horizontal or Vertical

        role : DisplayRole
           Each data item in data model may have many data elements
           associated with it. role, passed in by the View, indicates
           to the model which element of the data item is needed.

        section : int
            Column number

        Returns
        -------
        str | None
            Column description (depends on role and section)
        """

        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section == 0:
                    return "Office suit"
                elif section == 1:
                    return "virtual package type"
                elif section == 2:
                    return "version"
                elif section == 3:
                    return "marked for removal?"
                elif section == 4:
                    return "marked for upgrade?"
                elif section == 5:
                    return "marked for install?"
                else:
                    return None


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # -- Create GUI
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        self.main_view = QTableView()
        header = self.main_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        main_layout.addWidget(self.main_view)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(900, 550)

        # -- Create an object interacting with the data (Model)
        self.model = PackageMenuModel()
        # -- Link this object with the GUI (View/Controller)
        self.main_view.setModel(self.model)


app = QApplication()
window = MyWindow()
window.show()
sys.exit(app.exec())
