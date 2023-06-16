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
    def get_package_field(self, row: int, column: int):
        pass

    def set_package_field(self, row: int, column: int, value: bool):
        pass

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
        pass


class PackageMenuModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()

        # TODO: A test. Remove after creating proper model
        test_v_p = VirtualPackage("core-packages", "LibreOffice", "7.4")
        print(test_v_p)
        print(test_v_p.family)
        print(test_v_p.is_removable)

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
