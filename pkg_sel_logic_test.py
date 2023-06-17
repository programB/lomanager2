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

        # TODO: Temporary, hard coded list of new LibreOffice packages
        #       and CLipart available for install from repo.
        #       (+ version of those 2 software components)
        # TODO: such list should be passed to the __init__ method
        # TODO: This list should be either generated automatically based
        #       on hard coded latest available versions, a fixed list of
        #       supported languages and file naming convention
        #       or read in from a pre generated configuration file.
        self.latest_available_LO_version = "7.5"
        self.latest_available_clipart_version = "5.8"
        self.latest_available_packages = [
            VirtualPackage(
                "core-packages",
                "LibreOffice",
                self.latest_available_LO_version,
            ),
            VirtualPackage(
                "pl",
                "LibreOffice",
                self.latest_available_LO_version,
            ),
            VirtualPackage(
                "gr",
                "LibreOffice",
                self.latest_available_LO_version,
            ),
            VirtualPackage(
                "fr",
                "LibreOffice",
                self.latest_available_LO_version,
            ),
            VirtualPackage(
                "de",
                "LibreOffice",
                self.latest_available_LO_version,
            ),
            VirtualPackage(
                "jp",
                "LibreOffice",
                self.latest_available_LO_version,
            ),
            VirtualPackage(
                "it",
                "LibreOffice",
                self.latest_available_LO_version,
            ),
            VirtualPackage(
                "es",
                "LibreOffice",
                self.latest_available_LO_version,
            ),
            VirtualPackage(
                "core-packages",
                "Clipart",
                self.latest_available_clipart_version,
            ),
        ]

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
    def _allow_install(self, package: VirtualPackage) -> None:
        """Set install flags to allow install but don't mark for it

        Parameters
        ----------
        package : VirtualPackage
        """

        package.is_installable = True
        package.is_install_opt_visible = True
        package.is_install_opt_enabled = True

    def _allow_removal(self, package: VirtualPackage) -> None:
        """Set remove flags to allow removal but don't mark for it

        Parameters
        ----------
        package : VirtualPackage
        """

        package.is_removable = True
        package.is_remove_opt_visible = True
        package.is_remove_opt_enabled = True

    def _allow_upgrade(self, package: VirtualPackage) -> None:
        """Set upgrade flags to allow upgrade but don't mark for it

        Parameters
        ----------
        package : VirtualPackage
        """

        package.is_upgradable = True
        package.is_upgrade_opt_visible = True
        package.is_upgrade_opt_enabled = True

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

    def _get_newer(self, v1: str, v2: str) -> str:
        """Returns the newer of to versions passed

        Version strings are assumed to be dot
        separated eg. "4.5"
        These strings MUST follow the pattern
        but need not to be of the same length.
        Any version is newer then an empty string
        Empty string is returned is both v1 and v2
        empty strings.

        Parameters
        ----------
        v1 : str
          package version string eg. "9.1"

        v2 : str
          package version string eg. "9.1.2"

        Returns
        -------
        str
          newer of the v1 and v2, here 9.1.2 because it's newer then 9.1,
          or empty string.
        """

        if v1 != v2:
            if v1 == "":
                return v2
            elif v2 == "":
                return v1
            else:
                v1_int = [int(i) for i in v1.split(".")]
                v2_int = [int(i) for i in v2.split(".")]
                size_of_smaller_list = (
                    len(v2_int) if (len(v2_int) < len(v1_int)) else len(v1_int)
                )
                for i in range(size_of_smaller_list):
                    if v1_int[i] == v2_int[i]:
                        continue
                    elif v1_int[i] > v2_int[i]:
                        return v1
                    else:
                        return v2
        return v1  # ver1 = ver2

    def _get_newest_installed_LO_version(self) -> str:
        newest_verison = ""
        for package in self.packages:
            if (
                package.kind == "core-packages"
                and package.family == "LibreOffice"
                and package.version != ""
            ):
                newest_verison = self._get_newer(
                    package.version,
                    newest_verison,
                )
        return newest_verison

    def _set_all_flags_to_false(self, package: VirtualPackage) -> None:
        """Sets all bools (flags) in a virtual package False

        Parameters
        ----------
        package : VirtualPackage
        """

        # Get object's properties that start with "is_"
        props = [prop for prop in vars(package) if "is_" in prop]
        for prop in props:
            package.__dict__[prop] = False

    def _set_initial_state(self) -> None:
        """Decides on initial conditions for packages install/removal."""

        # 0) Disallow everything
        for package in self.packages:
            self._set_all_flags_to_false(package)
        for new_package in self.latest_available_packages:
            self._set_all_flags_to_false(new_package)

        # 1) Everything that is installed can be uninstalled
        for package in self.packages:
            self._allow_removal(package)

        # 2) Check if LibreOffice upgrade is possible
        #     a) What is the newest version of LibreOffice core-packages
        #        among those installed
        #        (in unlikely case there is more then 1 LibreOffice installed)
        self.newest_installed_LO_version = self._get_newest_installed_LO_version()

        if self.newest_installed_LO_version:  # a LibreOffice is installed
            # TODO: print for test purposes. Remove in final code
            print(f"Newest installed LO: {self.newest_installed_LO_version}")
            # b) latest version already installed
            if self.newest_installed_LO_version == self.latest_available_LO_version:
                # TODO: print for test purposes. Remove in final code
                print("Your LO is already at latest available version")
                # Allow for additional lang packs INSTALL coming...
                # ...FROM THE LIST of LATEST AVAILABLE PACKAGES
                # (LibreOffice only !!! OpenOffice office is not supported.)
                # - skip lang packs that are already installed (obvious)
                # (- skip core-packages as obviously it is not a lang pack)
                installed_langs = []
                for package in self.packages:
                    if (
                        package.family == "LibreOffice"
                        and package.version == self.latest_available_LO_version
                        and package.kind != "core-packages"
                    ):
                        installed_langs.append(package.kind)
                for new_package in self.latest_available_packages:
                    if (
                        new_package.family == "LibreOffice"
                        and new_package.version == self.latest_available_LO_version
                        and new_package.kind != "core-packages"
                        and new_package.kind not in installed_langs
                    ):
                        self._allow_install(new_package)
                        # TODO: This needs to moved to a proper place later on
                        #       eg. separate window.
                        #       Temporally append these packages to the
                        #       self.packages list so we can see the result
                        #       of this logic in the View
                        self.packages.append(new_package)

            # c) newer version available - allow upgrading
            elif self.latest_available_LO_version == self._get_newer(
                self.latest_available_LO_version,
                self.newest_installed_LO_version,
            ):
                # TODO: print for test purposes. Remove in final code
                print(
                    "LibreOffice version available from the repo "
                    f"({self.latest_available_LO_version}) is newer then "
                    f"the installed one ({self.newest_installed_LO_version}) "
                )
                # Allow upgrading the latest LibreOffice installed.
                # Older LibreOffice and OpenOffice versions
                # can only be uninstalled.
                for package in self.packages:
                    if (
                        package.family == "LibreOffice"
                        and package.version == self.newest_installed_LO_version
                    ):
                        self._allow_upgrade(package)

            # d) Something is wrong,
            #    installed version in newer then the latest available one
            else:
                # TODO: print for test purposes.
                #       REPLACE with logging and/or return status or exception
                print(
                    "Whoops! How did you manage to install LO that is newer "
                    f"({self.newest_installed_LO_version}) than the one in the"
                    f" repo ({self.latest_available_LO_version})?"
                )
                print(
                    "This program will not allow you to make any changes. "
                    "Please consult documentation."
                )
                # disallow everything
                for package in self.packages:
                    self._set_all_flags_to_false(package)
                for new_package in self.latest_available_packages:
                    self._set_all_flags_to_false(new_package)

        # 3) LO is not installed at all (OpenOffice may be present)
        else:
            print("No LO installed")
            # allow for LO install
            for new_package in self.latest_available_packages:
                if (
                    new_package.family == "LibreOffice"
                    and new_package.version == self.latest_available_LO_version
                ):
                    self._allow_install(new_package)
                    # TODO: This needs to moved to a proper place later on
                    #       eg. separate window.
                    #       Temporally append these packages to the
                    #       self.packages list so we can see the result
                    #       of this logic in the View
                    self.packages.append(new_package)

        # 4) Check if Clipart upgrade is possible
        #     a) What is the version of installed Clipart package
        for package in self.packages:
            if package.family == "Clipart":
                self.newest_installed_Clipart_version = package.version

        if self.newest_installed_Clipart_version:  # Clipart is installed
            # b) Installed Clipart already at latest version,
            #    nothing more needs to be done
            if (
                self.newest_installed_Clipart_version
                == self.latest_available_clipart_version
            ):
                # TODO: print for test purposes. Remove in final code
                print("Your Clipart is already at latest available version")
            # c) Newer version available - allow upgrading
            elif self.latest_available_clipart_version == self._get_newer(
                self.latest_available_clipart_version,
                self.newest_installed_Clipart_version,
            ):
                # TODO: print for test purposes. Remove in final code
                print(
                    "Clipart version available from the repo "
                    f"({self.latest_available_clipart_version}) is newer "
                    "then the installed one "
                    f"({self.newest_installed_Clipart_version})"
                )
                # Allow upgrade of the newest installed Clipart package
                for package in self.packages:
                    if package.family == "Clipart":
                        self._allow_upgrade(package)

            # d) Something is wrong,
            #    installed version in newer then the latest available one
            else:
                # TODO: print for test purposes.
                #       REPLACE with logging and/or return status or exception
                print(
                    "Whoops! How did you manage to install Clipart that is "
                    f"newer ({self.newest_installed_Clipart_version}) than "
                    "than the one in the repo "
                    f"({self.latest_available_clipart_version})?"
                )
                print(
                    "This program will not allow you to make any changes. "
                    "Please consult documentation."
                )
                # Disallow everything
                for package in self.packages:
                    self._set_all_flags_to_false(package)
                for new_package in self.latest_available_packages:
                    self._set_all_flags_to_false(new_package)

        # 5) Clipart is not installed at all
        else:
            # TODO: print for test purposes.
            print("No Clipart installed")
            # Allow for Clipart install
            for new_package in self.latest_available_packages:
                if (
                    new_package.family == "Clipart"
                    and new_package.version == self.latest_available_clipart_version
                ):
                    self._allow_install(new_package)
                    # TODO: This needs to moved to a proper place later on
                    #       eg. separate window.
                    #       Temporally append these packages to the
                    #       self.packages list so we can see the result
                    #       of this logic in the View
                    self.packages.append(new_package)


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
