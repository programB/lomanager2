from typing import Any

from pysidecompat import (
    QtGui,  # pyright: ignore
    QAbstractItemModel,  # pyright: ignore
    QAbstractTableModel,  # pyright: ignore
    QSortFilterProxyModel,  # pyright: ignore
    Qt,  # pyright: ignore
    QModelIndex,  # pyright: ignore
)

from lolangs import supported_langs


class PackageMenuViewModel(QAbstractTableModel):
    def __init__(self, main_logic, column_names):
        super().__init__()

        self._main_logic = main_logic
        self._column_names = column_names

        self.last_refresh_timestamp = 0
        self._package_list = []

    def get_package_list(self):
        """Rebuilds package list if it's outdated"""
        if (
            self._main_logic.refresh_timestamp > self.last_refresh_timestamp
            or self._package_list == []
        ):
            self._package_list = []
            self._main_logic.package_tree_root.get_subtree(self._package_list)
            self._package_list.remove(self._main_logic.package_tree_root)
            self.last_refresh_timestamp = self._main_logic.refresh_timestamp
        return self._package_list

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

        package = self.get_package_list()[row]

        if column == 0:
            pf_base, pf_vis, pf_enabled = (package.family, True, False)
        elif column == 1:
            pf_base, pf_vis, pf_enabled = (package.kind, True, False)
        elif column == 2:
            pf_base, pf_vis, pf_enabled = (
                supported_langs.get(package.kind),
                True,
                False,
            )
        elif column == 3:
            pf_base, pf_vis, pf_enabled = (package.version, True, False)
        elif column == 4:
            pf_base, pf_vis, pf_enabled = (
                package.is_marked_for_removal,
                package.is_remove_opt_visible,
                package.is_remove_opt_enabled,
            )
        elif column == 5:
            pf_base, pf_vis, pf_enabled = (
                package.is_marked_for_install,
                package.is_install_opt_visible,
                package.is_install_opt_enabled,
            )
        elif column == 6:
            pf_base, pf_vis, pf_enabled = (
                package.is_installed,
                True,
                True,
            )
        elif column == 7:
            pf_base, pf_vis, pf_enabled = (
                package.is_marked_for_download,
                True,
                True,
            )
        else:
            pf_base, pf_vis, pf_enabled = (None, None, None)

        if role == Qt.ItemDataRole.DisplayRole:
            # This will be either
            # strings for first 4 columns
            # or marked/unmarked condition for the rest
            return pf_base

        if role == Qt.ItemDataRole.CheckStateRole:
            # Check/Uncheck the cell in the View
            # based on package base field
            if column >= 4:
                if pf_base is True:
                    return Qt.CheckState.Checked
                if pf_base is False:
                    return Qt.CheckState.Unchecked

        if role == Qt.ItemDataRole.BackgroundRole:
            # Set background of the cell to darker
            # shade of grey if the operation is in
            # non enabled state
            if column >= 4:
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
            if column >= 4:
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
        """Returns number of rows the table has"""
        return len(self.get_package_list())

    def columnCount(self, index=QModelIndex()) -> int:
        """Returns the number of columns the table has"""
        return len(self._column_names)

    def headerData(self, section: int, orientation, role) -> str | None:
        """Returns name of each column in the table."""

        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            if section < self.columnCount():
                return self._column_names[section]
            return "not implemented"

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

        package = self.get_package_list()[row]

        # Only data in columns mark_for_removal|install
        # can be modified and they only accept boolean values
        # Also this method will not be called for other columns
        # because the flags() method already
        # prevents the user from modifying other columns.
        if column >= 4:
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
            # object holding the data
            if column == 4:
                is_logic_applied = self._main_logic.change_removal_mark(
                    package, value_as_bool
                )
            elif column == 5:
                is_logic_applied = self._main_logic.change_install_mark(
                    package, value_as_bool
                )
            else:
                is_logic_applied = False
            # ... and then inform the View that it should update its
            # state because data has changed.
            # Redraw ENTIRE View as the underlining PackageMenu logic
            # may have altered other cells - not just the one changed here.
            self.layoutChanged.emit()
            # Do not use:
            # self.dataChanged.emit(index, index, role)
            # as it causes only the altered cell to be redrawn by the View

            if is_logic_applied:  # desired state was set successfully
                return True
        return False  # invalid index OR something went wrong when setting

    def setHeaderData(self, section, orientation, value, role) -> bool:
        return super().setHeaderData(section, orientation, value, role)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        # Only allow mark_for_removal|install fields to be editable
        # Columns 0,1,2 and 3 can't be edited
        if index.column() >= 4:
            existing_flags = QAbstractItemModel.flags(self, index)
            return existing_flags | Qt.ItemFlag.ItemIsEditable
        return QAbstractItemModel.flags(self, index)

    # -- end "Setters" --


# Custom Proxy Model
class MainPackageMenuRenderModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(MainPackageMenuRenderModel, self).__init__(parent)

    def filterAcceptsRow(self, row, parent):
        if "Java" in self.sourceModel().index(row, 0, parent).data():
            return False
        if self.sourceModel().index(row, 1, parent).data() != "core-packages":
            return False
        return True


class LanguageMenuRenderModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(LanguageMenuRenderModel, self).__init__(parent)

    def filterAcceptsRow(self, row, parent):
        if self.sourceModel().index(row, 1, parent).data() == "core-packages":
            return False
        return True
