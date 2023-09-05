from typing import Any
from functools import cmp_to_key

from . pysidecompat import QtGui, QtWidgets, QtCore  # pyright: ignore
from configuration import supported_langs
from applogic.datatypes import compare_versions
import logging

log = logging.getLogger("lomanager2_logger")

column_idx = {
    "family": 0,
    "kind": 1,
    "language_code": 1,
    "language_name": 2,
    "version": 3,
    "marked_for_removal": 4,
    "marked_for_install": 5,
    "installed": 6,
    "marked_for_download": 7,
}


class SoftwareMenuModel(QtCore.QAbstractTableModel):
    """Main model translating app logic data into table representation"""

    def __init__(self, app_logic, column_names):
        super().__init__()

        self._app_logic = app_logic
        self._column_names = column_names

        self.last_rebuild_timestamp = 0
        self._package_list = []

    def get_package_list(self):
        """Rebuilds package list if it's outdated"""
        if (
            self._app_logic.rebuild_timestamp > self.last_rebuild_timestamp
            or self._package_list == []
        ):
            self._package_list = self._build_sorted_list(
                root=self._app_logic.package_tree_root
            )
            self.last_rebuild_timestamp = self._app_logic.rebuild_timestamp
        return self._package_list

    def _build_sorted_list(self, root):
        """Sort package list according to arbitrary criteria

        Any Java goes first followed by OpenOffice core packages sorted
        by version (newest first). Then LibreOffice core (LO cores sorted
        by version) immediately followed by its langpacks
        (sorted by country code). Finally Clipart core packages (newest first).
        """

        OOfficeS = []
        LOfficeS = []
        JavaS = [child for child in root.children if child.family == "Java"]
        if JavaS:
            java = JavaS[0]
            for office in java.children:
                if office.family == "OpenOffice":
                    OOfficeS.append(office)
                if office.family == "LibreOffice":
                    LOfficeS.append(office)
                    for lang in office.children:
                        LOfficeS.append(lang)

            # sort core packages by version
            OOfficeS.sort(key=cmp_to_key(compare_versions))
            LOfficeS.sort(key=cmp_to_key(compare_versions))
            # sort langpacks by language code
            # (this sorting is safe, already sorted core packages will not move)
            LOfficeS.sort(key=lambda p: p.kind if p.is_langpack() else "a")

        ClipartS = [c for c in root.children if c.family == "Clipart"]
        ClipartS.sort(key=cmp_to_key(compare_versions))

        return JavaS + OOfficeS + LOfficeS + ClipartS

    # -- "Getters" --
    def data(self, index, role) -> Any:
        """Returns data item as requested by the View.

        Parameters
        ----------
        index : QtCore.QModelIndex | QPeristentModelIndex
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

        packageS = self.get_package_list()
        if packageS:
            package = packageS[row]
        else:
            return

        if column == column_idx.get("family"):
            pf_base, pf_vis, pf_enabled = (package.family, True, False)
        elif column == column_idx.get("kind"):
            pf_base, pf_vis, pf_enabled = (package.kind, True, False)
        elif column == column_idx.get("language_name"):
            lang_code = package.kind
            pf_base, pf_vis, pf_enabled = (
                supported_langs.get(lang_code),
                True,
                False,
            )
        elif column == column_idx.get("version"):
            pf_base, pf_vis, pf_enabled = (package.version, True, False)
        elif column == column_idx.get("marked_for_removal"):
            pf_base, pf_vis, pf_enabled = (
                package.is_marked_for_removal,
                package.is_remove_opt_visible,
                package.is_remove_opt_enabled,
            )
        elif column == column_idx.get("marked_for_install"):
            pf_base, pf_vis, pf_enabled = (
                package.is_marked_for_install,
                package.is_install_opt_visible,
                package.is_install_opt_enabled,
            )
        elif column == column_idx.get("installed"):
            pf_base, pf_vis, pf_enabled = (
                package.is_installed,
                True,
                True,
            )
        elif column == column_idx.get("marked_for_download"):
            pf_base, pf_vis, pf_enabled = (
                package.is_marked_for_download,
                True,
                True,
            )
        else:
            pf_base, pf_vis, pf_enabled = (None, None, None)

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return pf_base

        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            # Display checked/uncheck box for cells holding boolen
            if isinstance(pf_base, bool):
                return (
                    QtCore.Qt.CheckState.Checked
                    if pf_base
                    else QtCore.Qt.CheckState.Unchecked
                )

        if role == QtCore.Qt.ItemDataRole.BackgroundRole:
            # Set background of the cell to darker
            # shade of grey if the operation disabled
            # but black if visibility is set to false
            if isinstance(pf_base, bool):
                if pf_enabled is False and pf_vis is True:
                    return QtGui.QColor("#484544")  # dark grey
                if pf_enabled is True and pf_vis is True:
                    return QtGui.QColor("#6d6967")  # light grey
                if pf_vis is False:
                    return QtGui.QColor("black")

        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            # Set text color in the cell
            # green - if the option is marked
            # red   - if the option is not marked
            # BUT
            # grey - if the operation is disabled
            if isinstance(pf_base, bool):
                if pf_enabled is False:
                    return QtGui.QColor("#635f5e")  # "middle" grey
                if pf_enabled is True:
                    if pf_base is True:
                        return QtGui.QColor("light green")
                    if pf_base is False:
                        return QtGui.QColor("dark red")

        if role == QtCore.Qt.ItemDataRole.FontRole:
            # Make text in the cell bold
            # if package enabled condition is True
            # (it will be default non-bold for when condition is False)
            if isinstance(pf_base, bool):
                font = QtGui.QFont()
                if pf_enabled is True:
                    font.setBold(True)
                    return font

        if role == QtCore.Qt.ItemDataRole.UserRole + 1:
            if isinstance(pf_base, str) or isinstance(pf_base, bool):
                return pf_base
            else:
                return ""

        if role == QtCore.Qt.ItemDataRole.UserRole + 2:
            return pf_vis

        if role == QtCore.Qt.ItemDataRole.UserRole + 3:
            return pf_enabled

        if role == QtCore.Qt.ItemDataRole.EditRole:
            # The type of delegate that is created by Qt automatically
            # if no custom one is provided is decided based on the type
            # of data returned in this EditRole
            # (eg. if str is returned here the delegate will be QLineEdit,
            # if it's bool it will be a QComboBox (with True and False values)
            # if it's int it will be a QSpinBox (with up-down arrows
            # increasing/decreasing int values by 1)
            # return str(pf_base)
            # return 1 if pf_base else 0
            return pf_base

    def rowCount(self, index) -> int:
        """Returns number of rows the table has"""
        return len(self.get_package_list())

    def columnCount(self, index=QtCore.QModelIndex()) -> int:
        """Returns the number of columns the table has"""
        return len(self._column_names)

    def headerData(self, section: int, orientation, role) -> str | None:
        """Returns name of each column in the table."""

        if (
            role == QtCore.Qt.ItemDataRole.DisplayRole
            and orientation == QtCore.Qt.Orientation.Horizontal
        ):
            if section < self.columnCount():
                return self._column_names[section]
            return "not implemented"

    # -- end "Getters" --

    # -- "Setters" --
    # To enable editing, the following functions must be implemented correctly:
    # setData(), setHeaderData(), flags()
    def setData(self, index, value, role) -> bool:
        """Attempts to set install or remove flag of a package

        Tries to set the flag of the package indicated by the index
        (package flag: is_marked_for_removal or is_marked_for_install)
        by calling app logic methods

        Parameters
        ----------
        index : QtCore.QModelIndex | QPeristentModelIndex
            Points to a specific data item in data model

        value : bool
        T/F - mark/unmark for removal or install

        role : DisplayRole
           Each data item in data model may have many data elements
           associated with it. role, passed in by the View, indicates
           to the model which element of the data item is needed.

        Returns
        -------
        bool
          True: logic has successfully marked the package
          False: non flag column, package logic failed, index not valid
        """

        row = index.row()
        column = index.column()

        packageS = self.get_package_list()
        if packageS:
            package = packageS[row]
        else:
            return False

        # Only data in columns marked_for_removal|install
        # can be modified and they only accept boolean values
        # Also this method will not be called for other columns
        # because the flags() method already
        # prevents the user from modifying other columns.
        if not isinstance(value, bool):
            log.error(f"expected boolean to set mark state, received {type(value)}")

        if index.isValid() and role == QtCore.Qt.ItemDataRole.EditRole:
            if column == column_idx.get("marked_for_removal"):
                # Critically important! Warn views/viewmodels that underlying
                # data will change
                self.layoutAboutToBeChanged.emit()

                # Request data change from the applogic
                is_logic_applied = self._app_logic.change_removal_mark(
                    package,
                    value,
                )

                # Tell the views to redraw themselves ENTIRELY
                # (not just the cell changed here)
                self.layoutChanged.emit()

                # Finally
                return is_logic_applied

            elif column == column_idx.get("marked_for_install"):
                self.layoutAboutToBeChanged.emit()
                is_logic_applied = self._app_logic.change_install_mark(
                    package,
                    value,
                )
                self.layoutChanged.emit()
                return is_logic_applied
            else:
                return False
        return False

    def setHeaderData(self, section, orientation, value, role) -> bool:
        return super().setHeaderData(section, orientation, value, role)

    def flags(self, index):
        """Tells which column/rows can be changed"""
        if index.isValid() is False:
            return QtCore.Qt.ItemFlag.ItemIsEnabled
        # Only allow marked_for_removal|install fields to be editable
        if index.column() == column_idx.get(
            "marked_for_removal"
        ) or index.column() == column_idx.get("marked_for_install"):
            existing_flags = QtCore.QAbstractItemModel.flags(self, index)
            return existing_flags | QtCore.Qt.ItemFlag.ItemIsEditable
        return QtCore.QAbstractItemModel.flags(self, index)

    # -- end "Setters" --


# Custom Proxy Models
class SoftwareMenuRenderModel(QtCore.QSortFilterProxyModel):
    def __init__(self, model, parent=None):
        super(SoftwareMenuRenderModel, self).__init__(parent)
        self.setSourceModel(model)

    def filterAcceptsRow(self, row, parent):
        sm = self.sourceModel
        if "Java" in sm().index(row, column_idx.get("family"), parent).data():
            # don't show Java
            return False
        elif (
            sm().index(row, column_idx.get("kind"), parent).data() == "core-packages"
            or sm().index(row, column_idx.get("installed"), parent).data() is True
        ):
            # show any core package and any installed lang package
            return True
        else:
            return False


class LanguageMenuRenderModel(QtCore.QSortFilterProxyModel):
    def __init__(self, model, parent=None):
        super(LanguageMenuRenderModel, self).__init__(parent)
        self.setSourceModel(model)
        self.setSortRole(QtCore.Qt.ItemDataRole.UserRole + 1)
        self.setFilterKeyColumn(-1)

    def filterAcceptsRow(self, row, parent):
        sm = self.sourceModel
        if (
            sm().index(row, column_idx.get("kind"), parent).data() != "core-packages"
            and sm().index(row, column_idx.get("installed"), parent).data() is False
        ):
            # show any NOT installed lang package
            return True
        return False
