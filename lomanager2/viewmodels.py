from typing import Any
from PySide6 import QtGui

from PySide6.QtCore import (
    QAbstractItemModel,
    QAbstractTableModel,
    Qt,
)


class PackageMenuViewModel(QAbstractTableModel):
    def __init__(self, main_logic):
        super().__init__()

        self._main_logic = main_logic

    # -- start "Getters" --
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
        pf_base, pf_vis, pf_enabled = self._main_logic.get_PackageMenu_field(
            row, column
        )

        if role == Qt.ItemDataRole.DisplayRole:
            # This will be either
            # strings for first 3 columns
            # or marked/unmarked condition for the later 3
            return pf_base

        if role == Qt.ItemDataRole.CheckStateRole:
            # Check/Uncheck the cell in the View
            # based on package base field
            if column >= 3:
                if pf_base is True:
                    return Qt.CheckState.Checked
                if pf_base is False:
                    return Qt.CheckState.Unchecked

        if role == Qt.ItemDataRole.BackgroundRole:
            # Set background of the cell to darker
            # shade of grey if the operation is in
            # non enabled state
            if column >= 3:
                if pf_enabled is False and pf_vis is True:
                    return QtGui.QColor("#484544")  # dark grey
                if pf_enabled is True and pf_vis is True:
                    return QtGui.QColor("#6d6967")  # light grey
                if pf_vis is False:
                    return QtGui.QColor("black")

        if role == Qt.ItemDataRole.ForegroundRole:
            # Set text color in the cell
            # green - if the option is marked
            # red   - if the option is not marked
            # BUT
            # grey - if the operation is in non enabled state
            if column >= 3:
                if pf_enabled is False:
                    return QtGui.QColor("#635f5e")  # "middle" grey
                if pf_enabled is True:
                    if pf_base is True:
                        return QtGui.QColor("light green")
                    if pf_base is False:
                        return QtGui.QColor("dark red")

        if role == Qt.ItemDataRole.FontRole:
            # Make text in the cell bold
            # if package enabled condition is True
            # (it will be default non-bold for when condition is False)
            font = QtGui.QFont()
            if column >= 3:
                if pf_enabled is True:
                    font.setBold(True)
                    return font

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

        # TODO: should this be done this way?
        #       app logic does not have any notion
        #       of "rows" or their number.
        #       It may be just the issue of naming
        #       like main_logic.get_PackageMenu_number_of_packages
        return self._main_logic.get_PackageMenu_row_count()

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

        # TODO: this defiantly should not be done this way
        #       main_logic does not have any notion of columns!
        #       The translation between what the data are and how to
        #       represent them as a table should be done here.
        #       Leaving for now as this requires changes
        #       in MainLogic and PackageMenu
        return self._main_logic.get_PackageMenu_column_count()

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
                elif section == 6:
                    return "is installed?"
                else:
                    return None

    # -- end "Getters" --

    # -- start "Setters" --
    # To enable editing, the following functions must be implemented correctly:
    # setData(), setHeaderData(), flags()
    def setData(self, index, value, role) -> bool:
        """Attempts to set data in the PackageMenu based on user input

        Set package's flag (T/F) indicated by index
        (effectively row and column)
        by calling PackageMenu method set_package_field()

        Parameters
        ----------
        index : QModelIndex | QPeristentModelIndex
            Points to a specific data item in data model

        value : str
          Although any string can be provided only strings: "True", "False",
          "1", "0" representing booleans will have effect.

        role : DisplayRole
           Each data item in data model may have many data elements
           associated with it. role, passed in by the View, indicates
           to the model which element of the data item is needed.

        Returns
        -------
        bool
          True: PackageMenu successfully applied package logic
          False: non flag column, package logic failed, index not valid
        """

        row = index.row()
        column = index.column()

        # Only data in columns mark_for_removal|upgrade|install
        # can be modified and they only accept boolean values
        # Also this method will not be called for other columns
        # because the flags() method already
        # prevents the user from modifying other columns.
        if column >= 3:
            if value.upper() == "TRUE" or value == "1":
                value_as_bool = True
            elif value.upper() == "FALSE" or value == "0":
                value_as_bool = False
            else:
                return False
        else:
            return False

        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            # This is the place to send the entered value to the underlining
            # object holding the data (PackageMenu) ...
            s = self._main_logic.set_PackageMenu_field(
                row,
                column,
                value_as_bool,
            )

            # ... and then inform the View that it should update its
            # state because data has changed.
            # Redraw ENTIRE View as the underlining PackageMenu logic
            # may have altered other cells - not just the one changed here.
            self.layoutChanged.emit()
            # Do not use:
            # self.dataChanged.emit(index, index, role)
            # as it causes only the altered cell to be redrawn by the View

            if s:  # desired state was set successfully
                return True
        return False  # invalid index OR something went wrong when setting

    def setHeaderData(self, section, orientation, value, role) -> bool:
        return super().setHeaderData(section, orientation, value, role)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        # Only allow mark_for_removal|upgrade|install fields to be editable
        # Columns 0,1 and 3 can't be edited
        if index.column() >= 3:
            existing_flags = QAbstractItemModel.flags(self, index)
            return existing_flags | Qt.ItemFlag.ItemIsEditable
        return QAbstractItemModel.flags(self, index)

    # -- end "Setters" --
