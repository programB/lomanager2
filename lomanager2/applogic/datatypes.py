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
        - the package was marked for specific operation
          (install/removal/upgrade)
        - if it can be marked for such operation,
        - should the operation be visible to the user and
        - should it be in enabled state
          (or disabled even if it is visible).

    Each package also has the
        - is_to_be_downloaded
    flag that signal whether packages associated with
    this virtual package need to be downloaded from the internet.

    Attributes
    ----------
    kind : str
    family :str
    version : str
    real_packages = list[dict[str, int]]
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
    is_to_be_downloaded : bool
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

        self.kind = kind
        self.family = family
        self.version = version
        self.real_packages = [{"rpm name": "", "size": 0}]  # size in kilobytes
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
        # Action flags
        self.is_to_be_downloaded = False


class SignalFlags(object):
    def __init__(self) -> None:
        self.block_viewing_installed = False
        self.block_viewing_available = False
        self.block_removal = False
        self.block_network_install = False
        self.block_local_copy_install = False
        self.block_checking_4_updates = False
        self.ready_to_apply_changes = False
        self.keep_packages = False
        self.force_download_java = False
