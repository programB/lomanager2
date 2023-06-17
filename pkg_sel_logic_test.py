import sys
from typing import Any, Tuple
from PySide6 import QtGui

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableView,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from PySide6.QtCore import (
    QAbstractItemModel,
    QAbstractTableModel,
    Qt,
)


class VirtualPackage(object):
    """VirtualPackage represents a bundle of rpm packages operated as one

    A bundle is one or more rpm packages that are or should be
    installed/uninstalled together without side effects and are units
    package selection logic which decides what rpm(s) should
    be actually installed/removed.

    There are 2 kinds of these virtual packages / bundles:
        - "core-packages" is the package representing OpenOffice
        or LibreOffice base package and base help package.
        These are always installed/removed together and provide required
        and sufficient functionality to use the Office suite.

        This kind of package also represents a single rpm package with
        Clipart library.

        - "<language code>" this virtual package represents a bundle of
        localization rpm packages for specific language that is
        a language pack and a language help pack.

    Each virtual package has a state, represented by a number of
    flags/attributes. These describe whether:
        - the package was marked for specific operation
          (install/removal/upgrade)
        - if it can be marked for such operation,
        - should the operation be visible to the user and
        - should it be in enabled state
          (or disabled even if it is visible).

    Attributes
    ----------
    kind : str
    family :str
    version : str
    is_removable : bool
    is_remove_opt_visible : bool
    is_remove_opt_enabled : bool
    is_marked_for_removal : bool
    is_upgradable : bool
    is_upgrade_opt_visible : bool
    is_upgrade_opt_enabled : bool
    is_marked_for_upgrade : bool
    is_installable : bool
    is_install_opt_visible : bool
    is_install_opt_enabled : bool
    is_marked_for_install : bool
    """

    def __init__(self, kind: str, family: str, version: str) -> None:
        """Creates VirtualPackage object

        Parameters
        ----------
        kind : str
            The type of virtual package to create: "core-packages"
            or a specific language code like. "jp" or "fr"

        family : str
            Software this virtual package represents: "OpenOffice",
            "LibreOffice" or "Clipart"

        version : str
            Version of the package. Dot separated format eg. "2.4.1"
        """

        self.kind = kind
        self.family = family
        self.version = version
        # Remove flags
        self.is_removable = False
        self.is_remove_opt_visible = False
        self.is_remove_opt_enabled = False
        self.is_marked_for_removal = False
        # Upgrade flags
        self.is_upgradable = False
        self.is_upgrade_opt_visible = False
        self.is_upgrade_opt_enabled = False
        self.is_marked_for_upgrade = False
        # Install flags
        self.is_installable = False
        self.is_install_opt_visible = False
        self.is_install_opt_enabled = False
        self.is_marked_for_install = False


class PackageMenu(object):
    def __init__(self) -> None:
        # Temporary, hard coded list of software "installed" in the system
        # TODO: such list should be passed to the __init__ method
        #       from the "Gather system information" procedure
        #       (see the flowchart)
        self.found_software = [
            ["OpenOffice", "2.0"],
            ["OpenOffice", "2.4", "pl", "gr"],
            ["LibreOffice", "3.0.0", "fr", "de"],
            ["LibreOffice", "7.5", "jp", "pl"],
            ["Clipart", "5.3"],
        ]
        for item in self.found_software:
            print(item)

        # Data store representing items in the menu
        self.packages = []

        # Initialize PackageMenu object
        # a) Build a list of virtual packages from the list
        #    of packages installed in the system.
        self._build_package_list()
        # b) Set initial state of the menu by analyzing package
        #    dependencies and system state to decide
        #    what the user can/cannot do.
        self._set_initial_state()

    # Public methods
    def get_package_field(self, row: int, column: int) -> Tuple[Any, Any, Any]:
        """Gets any field in the package menu (at row and column)

        This method is used to represent underlying package data as
        a table with rows representing each package the user can request
        operation on and various columns showing the status of this operations.
        This virtual table is thought to consist of 6 columns (0-5):
        |Software name|package type|version|...
        ...|removal flags|upgrade flags|install flags|

        Each row-column combination leads to a field that is described by
        a tuple of 3 parameters. For columns 0-2 it is the string (either kind
        family or version) and 2 filler boolean values that don't carry meaning
        For columns 3-5 returned is a tuple of 3 (out of 4 existing) flags
        of the virtual package shown in this row.
        These are accordingly:
            is_marked_for_(removal/upgrade/install)
            is_(remove/upgrade/install)_opt_visible
            is_(remove/upgrade/install)_opt_enabled

        virtual package flags:
            removable/upgradable/installable
            are treated as private and never returned


        Parameters
        ----------
        row : int
          row of the package list
        column : int
          column of the package list

        Returns
        -------
        Tuple[Any, Any, Any]
          (string, bool, bool) - for columns 0,1,2 (bools are just fillers)
          (bool, bool, bool) - for columns 3,4,5 (visible) package flags
        """

        package = self.packages[row]
        if column == 0:
            return (package.family, True, False)
        elif column == 1:
            return (package.kind, True, False)
        elif column == 2:
            return (package.version, True, False)
        elif column == 3:
            return (
                package.is_marked_for_removal,
                package.is_remove_opt_visible,
                package.is_remove_opt_enabled,
            )
        elif column == 4:
            return (
                package.is_marked_for_upgrade,
                package.is_upgrade_opt_visible,
                package.is_upgrade_opt_enabled,
            )
        elif column == 5:
            return (
                package.is_marked_for_install,
                package.is_install_opt_visible,
                package.is_install_opt_enabled,
            )
        else:
            return (None, None, None)

    def set_package_field(self, row: int, column: int, value: bool) -> bool:
        # TODO: This naive flags setting is for testing purposes only
        #       Replace with proper code.

        # TODO: Package selection logic should be applied in this method

        # TODO: this method should return True/False to provide GUI with
        #       some information if the package selection logic failed
        #       to set the desired state (for any reason)
        is_logic_applied = False
        package = self.packages[row]
        if column == 3:
            package.is_marked_for_removal = value
            is_logic_applied = True
        elif column == 4:
            package.is_marked_for_upgrade = value
            is_logic_applied = True
        elif column == 5:
            package.is_marked_for_install = value
            is_logic_applied = False
        else:
            is_logic_applied = False
        return is_logic_applied

    def get_row_count(self) -> int:
        """Returns number of rows of the packages menu

        Returns
        -------
        int
          number of rows
        """
        return len(self.packages)

    def get_column_count(self) -> int:
        """Returns number of columns of the package menu

        Returns
        -------
        int
          Currently package menu is thought as having 6 columns
        """
        return 6

    # Private methods
    def _build_package_list(self) -> None:
        """Builds a list of virtual packages based on installed ones."""
        for office_suit in self.found_software:
            family = office_suit[0]
            version = office_suit[1]
            core_packages = VirtualPackage(
                "core-packages",
                family,
                version,
            )
            self.packages.append(core_packages)
            for lang in office_suit[2:]:
                lang_pkg = VirtualPackage(lang, family, version)
                self.packages.append(lang_pkg)

    def _set_initial_state(self) -> None:
        """Decides on initial conditions for packages install/removal."""
        # TODO: Package flags set below just for GUI testing purposes.
        #       Remove when writing proper code.
        for package in self.packages:
            if package.family == "OpenOffice":
                package.is_removable = True
                package.is_remove_opt_enabled = True
                package.is_marked_for_removal = True
            if package.family == "Clipart":
                package.is_removable = True
                package.is_remove_opt_enabled = False
                package.is_marked_for_removal = True
                package.is_upgradable = True
                package.is_upgrade_opt_enabled = True
                package.is_marked_for_upgrade = False


class PackageMenuModel(QAbstractTableModel):
    def __init__(self, package_menu=None):
        super().__init__()

        # Create or reference an object concerned
        # with the logic of package operations
        if package_menu is None:
            self.package_menu = PackageMenu()
        else:
            self.package_menu = package_menu

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
        pf_base, pf_visible, pf_enabled = self.package_menu.get_package_field(
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
                if pf_enabled is False:
                    return QtGui.QColor("#484544")  # dark grey
                if pf_enabled is True:
                    return QtGui.QColor("#6d6967")  # light grey

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

        return self.package_menu.get_row_count()

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

        return self.package_menu.get_column_count()

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

        # TODO: Printing just for testing. Remove when not needed
        print(f"you entered: {value} (type {type(value)})")

        # Only data in columns mark_for_removal|upgrade|install
        # can be modified and they only accept boolen values
        # Also this method will not be called for other columns
        # because the flags() method already
        # prevents the user from modifying other columns.
        if column >= 3:
            if value.upper() == "TRUE" or value == "1":
                value_as_bool = True
            if value.upper() == "FALSE" or value == "0":
                value_as_bool = False
        else:
            return False

        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            # This is the place to send the entered value to the underlining
            # object holding the data (PackageMenu) ...
            s = self.package_menu.set_package_field(row, column, value_as_bool)

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
