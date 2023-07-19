import weakref


class VirtualPackage(object):
    """VirtualPackage represents a bundle of rpm packages operated as one

    A bundle is one or more rpm packages that are or should be
    installed/uninstalled together without side effects.
    Such a VirtualPackage is a unit on package selection logic operates.

    Each VirtualPackage objects holds the information of what real
    rpm packages it represents and how much disk space each of them
    occupies when installed.

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
        - the package is currently installed
        - the package was marked for specific operation
          (install/removal/upgrade)
        - if it can be marked for such operation,
        - should the operation be visible to the user and
        - should it be in enabled state
          (or disabled even if it is visible).

    Each package also has the
        - is_marked_for_download
    flag that signal whether packages associated with
    this virtual package need to be downloaded from the internet.

    Attributes
    ----------
    kind : str
    family :str
    version : str
    real_packages = list[dict[str, int]]
    is_installed: bool
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
    is_marked_for_download : bool
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
            "LibreOffice", "Clipart" or "Java"

        version : str
            Version of the package. Dot separated format eg. "2.4.1"
        """
        self._parent = None
        self.children = []

        self.kind = kind
        self.family = family
        self.version = version
        self.real_packages = [{"rpm name": "", "size": 0}]  # size in kilobytes
        self.download_size = 0  # size in kilobytes
        # State flags
        self.is_installed = False
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
        # Download flags
        self.is_marked_for_download = False

    @property
    def parent(self):
        return self._parent if self._parent is None else self._parent()

    @parent.setter
    def parent(self, virtual_package):
        self._parent = weakref.ref(virtual_package)

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def get_subtree(self, nodeslist):
        if self.children:
            for child in self.children:
                child.get_subtree(nodeslist)
        nodeslist.append(self)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return (
                other.kind == self.kind
                and other.family == self.family
                and other.version == self.version
            )
        else:
            return False

    def allow_install(self) -> None:
        """Set install flags to allow install but don't mark for it"""

        self.is_installable = True
        self.is_install_opt_visible = True
        self.is_install_opt_enabled = True

    def allow_removal(self) -> None:
        """Set remove flags to allow removal but don't mark for it"""

        self.is_removable = True
        self.is_remove_opt_visible = True
        self.is_remove_opt_enabled = True

    def allow_upgrade(self) -> None:
        """Set upgrade flags to allow upgrade but don't mark for it"""

        self.is_upgradable = True
        self.is_upgrade_opt_visible = True
        self.is_upgrade_opt_enabled = True

    def is_langpack(self) -> bool:
        if self.kind != "core-packages" and self.family == "LibreOffice":
            return True
        else:
            return False

    def disallow_operations(self) -> None:
        """Sets all non state flags in virtual package False"""

        # Get object's properties that start with "is_"
        props = [prop for prop in vars(self) if "is_" in prop]
        for prop in props:
            if "is_installed" in prop:
                pass
            else:
                self.__dict__[prop] = False


class SignalFlags(object):
    def __init__(self) -> None:
        self.block_viewing_installed = False
        self.block_viewing_available = False
        self.block_removal = False
        self.block_network_install = False
        self.block_local_copy_install = False
        self.block_checking_4_updates = False
        self.ready_to_apply_changes = False
