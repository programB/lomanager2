import time  # TODO: just for the tests
import re
import pathlib
import urllib.request, urllib.error
from copy import deepcopy
import configuration
from configuration import logging as log
from typing import Any, Tuple, Callable
from . import PCLOS
from .datatypes import VirtualPackage, SignalFlags
from .callbacks import (
    OverallProgressReporter,
    progress_closure,
    progress_description_closure,
    statusfunc_closure,
)


class MainLogic(object):
    # Only 1 objects of this class will exists.
    # So this could have been done by placing
    # the variables, statements and functions directly in a module.
    # But this would then run these at module import
    # and I don't want to put import statements
    # in the middle of a code or brake code's intelligibility
    # by importing some logic at the top of the main file.
    def __init__(self) -> None:
        # 1) Create needed directories
        PCLOS.create_directories()

        # 2) Create state objects
        self._warnings = [""]
        self.global_flags = SignalFlags()
        self._package_tree = VirtualPackage.__new__(VirtualPackage)
        self._package_menu = ManualSelectionLogic.__new__(ManualSelectionLogic)

        # 3) Run flags_logic
        self.any_limitations, self._warnings = self._flags_logic()
        if self.any_limitations is True:
            log.error("System not ready for all operations:")
            for i, warning in enumerate(self._warnings):
                log.error(f"{i+1}: {warning}")

        # 4) Gather system information
        #           AND
        # 5) Initialize state objects
        #
        #   (done in separate, reusable method)
        self.refresh_state()

    # -- Public interface for MainLogic

    def get_PackageMenu_field(self, row, column):
        # self._package_menu.DO_SOMETHING
        return self._package_menu.get_package_field(row, column)

    # TODO: This method should either be renamed or not exist
    #       See rowCount method of PackageMenuViewModel
    def get_PackageMenu_row_count(self):
        return self._package_menu.get_row_count()

    # TODO: This method should not exist
    #       See coulmnCount method of PackageMenuViewModel
    def get_PackageMenu_column_count(self):
        return self._package_menu.get_column_count()

    def set_PackageMenu_field(self, row, column, value_as_bool):
        # 1) call PackageMenu method to
        pms = self._package_menu.set_package_field(row, column, value_as_bool)
        # 2) above always creates a list of real rpm packages that need
        #    to be removed/installed and the space they occupy/will occupy
        # 3) compare the space requirement of new state with available
        #    free disk space
        total_space_needed = (
            self._package_menu.package_delta["space_to_be_used"]
            - self._package_menu.package_delta["space_to_be_freed"]
        )
        space_available = PCLOS.free_space_in_dir(configuration.download_dir)
        # 4) set "ready for state transition flag" (T/F) accordingly
        # 5) add warning message to self._warnings if not enough space
        if space_available < total_space_needed:
            self.global_flags.ready_to_apply_changes = False
            self._warnings = [
                {
                    "explanation": "Insufficient disk space for operation.",
                    "data": "Space needed: "
                    + str(total_space_needed)
                    + "space available: "
                    + str(space_available),
                }
            ]
        else:
            self.global_flags.ready_to_apply_changes = True
        return pms

    def get_warnings(self):
        warnings = deepcopy(self._warnings)
        self._clear_warnings()
        return warnings

    def _clear_warnings(self):
        self._warnings = [""]

    def apply_changes(self, *args, **kwargs):
        # Callback function for reporting the status of the procedure
        statusfunc = statusfunc_closure(callbacks=kwargs)

        # Check if we can proceed with applying changes
        if self.global_flags.ready_to_apply_changes is False:
            return statusfunc(isOK=False, msg="Not ready to apply changes.")

        # Check if normal installation was not blocked
        if self.global_flags.block_network_install is True:
            return statusfunc(isOK=False, msg="Modifications were blocked.")

        # Check if keep_package option was passed
        if "keep_packages" in kwargs.keys():
            keep_packages = kwargs["keep_packages"]
        else:
            return statusfunc(isOK=False, msg="keep_packages argument is obligatory")

        # Check if force_java_download option was passed
        if "force_java_download" in kwargs.keys():
            force_java_download = kwargs["force_java_download"]
        else:
            return statusfunc(
                isOK=False, msg="force_java_download argument is obligatory"
            )

        # We are good to go
        # Create helper objects for progress reporting
        progress = progress_closure(callbacks=kwargs)
        progress_description = progress_description_closure(callbacks=kwargs)
        step = OverallProgressReporter(total_steps=11, callbacks=kwargs)

        # Mark Java for download if the user requests that
        java_package = [c for c in self._package_tree.children if "Java" in c.family][0]
        if force_java_download is True:
            java_package.is_marked_for_download = True

        # Block any other calls of this function...
        self.global_flags.ready_to_apply_changes = False
        # ...and proceed with the procedure
        log.info("Applying changes...")
        status = self._install(
            keep_packages=keep_packages,
            statusfunc=statusfunc,
            progress_description=progress_description,
            progress_percentage=progress,
            step=step,
        )
        return status

    def install_from_local_copy(self, *args, **kwargs):
        # Callback function for reporting the status of the procedure
        statusfunc = statusfunc_closure(callbacks=kwargs)

        # Check if we can proceed with applying changes
        if self.global_flags.ready_to_apply_changes is False:
            return statusfunc(isOK=False, msg="Not ready to apply changes.")

        # Check if local copy installation was not blocked
        if self.global_flags.block_local_copy_install is True:
            return statusfunc(isOK=False, msg="Local copy installation was blocked.")

        # Check if local copy directory was passed
        if "local_copy_folder" in kwargs.keys():
            local_copy_directory = kwargs["local_copy_folder"]
        else:
            return statusfunc(
                isOK=False, msg="local_copy_folder argument is obligatory"
            )

        # We are good to go
        # Create helper objects for progress reporting
        progress = progress_closure(callbacks=kwargs)
        progress_description = progress_description_closure(callbacks=kwargs)
        step = OverallProgressReporter(total_steps=11, callbacks=kwargs)

        # Block any other calls of this function...
        self.global_flags.ready_to_apply_changes = False
        # ...and proceed with the procedure
        log.info("Applying changes...")
        status = self._local_copy_install_procedure(
            local_copy_directory=local_copy_directory,
            statusfunc=statusfunc,
            progress_description=progress_description,
            progress_percentage=progress,
            step=step,
        )
        return status

    def refresh_state(self):
        # -- NEW Logic --
        # 1) Query for installed software
        installed_vps = self._detect_installed_software()
        # 2) Query for available software
        available_vps = self._get_available_software()
        # 3) Create joint list of packages
        complement = [p for p in available_vps if p not in installed_vps]
        joint_package_list = installed_vps + complement
        # 5) build package dependency tree
        root_node = self._build_dependency_tree(joint_package_list)
        log.debug("TREE \n" + root_node.tree_representation())
        # 4) apply virtual packages initial state logic
        (
            latest_Java,
            newest_Java,
            latest_LO,
            newest_LO,
            latest_Clip,
            newest_Clip,
        ) = self._set_packages_initial_state(root_node)
        # 6) Replace the old state of the list with the new one
        # self._virtual_packages = joint_package_list
        # 7) the same with package tree
        self._package_tree = root_node
        # -- --------- --

        self._package_menu = ManualSelectionLogic(
            root_node=self._package_tree,
            latest_Java=latest_Java,
            newest_Java=newest_Java,
            latest_LO=latest_LO,
            newest_LO=newest_LO,
            latest_Clip=latest_Clip,
            newest_Clip=newest_Clip,
        )
        self.global_flags.ready_to_apply_changes = True

    # -- end Public interface for MainLogic

    # -- Private methods of MainLogic
    def _build_dependency_tree(self, packageS: list[VirtualPackage]) -> VirtualPackage:
        master_node = VirtualPackage("master-node", "", "")
        current_parent = master_node
        # 1st tier: Link Java and Clipart to top level package
        already_handled = []
        for package in packageS:
            if package.family == "Clipart" and package.kind == "core-packages":
                current_parent.add_child(package)
                already_handled.append(package)
        packageS = [p for p in packageS if p not in already_handled]

        for package in packageS:
            if package.family == "Java" and package.kind == "core-packages":
                current_parent.add_child(package)
                already_handled.append(package)
                current_parent = package
        # and remove from packageS list
        # Warning: packageS now becomes and independent copy of original
        #          packageS passed in the argument so this selective
        #          copying is not removing items from the original list
        packageS = [p for p in packageS if p not in already_handled]

        # 2nd tier: Link OO and LO core packages to Java
        Office_parents = []
        for package in packageS:
            if (
                package.family == "OpenOffice" or package.family == "LibreOffice"
            ) and package.kind == "core-packages":
                current_parent.add_child(package)
                already_handled.append(package)
                Office_parents.append(package)
        # and remove from packageS list
        packageS = [p for p in packageS if p not in already_handled]

        # 3rd tier: Link OO and LO lang packages to their parent core packages
        for package in packageS:
            if package.kind != "core-packages":
                for matching_parent in Office_parents:
                    if matching_parent.version == package.version:
                        matching_parent.add_child(package)
                        already_handled.append(package)
        # and remove from packageS list
        packageS = [p for p in packageS if p not in already_handled]
        # At this point packageS should be empty
        # log.debug(f"packageS: {packageS}")

        # log.debug("\n" + master_node.tree_representation())
        return master_node

    def _set_packages_initial_state(
        self,
        root: VirtualPackage,
    ) -> tuple[str, str, str, str, str, str]:
        """Decides on initial conditions for packages install/removal."""

        # For each software component (Java, LibreOffice, Clipart) check:
        # - the newest installed version
        # - the latest available version from the repo
        newest_installed_Java_version = ""
        java = [c for c in root.children if "Java" in c.family][0]
        if java.is_installed:
            newest_installed_LO_version = java.version
        latest_available_Java_version = configuration.latest_available_java_version
        # java install/remove/upgrade options are never visible

        newest_installed_LO_version = ""
        LibreOfficeS = [c for c in java.children if "LibreOffice" in c.family]
        for office in LibreOfficeS:
            if office.is_installed:
                newest_installed_LO_version = self._return_newer_ver(
                    office.version,
                    newest_installed_LO_version,
                )
        latest_available_LO_version = configuration.latest_available_LO_version

        newest_installed_Clipart_version = ""
        clipartS = [c for c in root.children if "Clipart" in c.family]
        for clipart in clipartS:
            if clipart.is_installed:
                newest_installed_Clipart_version = clipart.version
        latest_available_Clipart_version = (
            configuration.latest_available_clipart_version
        )

        # 0) Disallow everything
        # This is already done - every flag in VirtualPackage is False by default

        # 1) Everything that is installed can be uninstalled
        all_packages = []
        root.get_subtree(all_packages)
        for package in all_packages:
            if package.is_installed:
                package.allow_removal()

        # 2) Mark any OpenOffice package found for unconditional removal
        #    (mark for removal and prevent the user from unmarking them)
        for package in all_packages:
            if package.family == "OpenOffice":
                package.is_marked_for_removal = True
                package.is_remove_opt_enabled = False
                package.is_remove_opt_visible = True

        # 3)
        # Java installation/upgrading or removal are not supported
        # by this program. This should be done by a proper package manager
        # like Synaptic

        # 4) Check options for LibreOffice
        #
        # LibreOffice is installed
        if newest_installed_LO_version:
            log.debug(f"Newest installed LO: {newest_installed_LO_version}")

            # a) is latest version already installed ?
            if newest_installed_LO_version == latest_available_LO_version:
                log.debug("Installed LO is already at latest available version")
                # Allow for additional lang packs installation
                # - LibreOffice only !!! OpenOffice office is not supported.
                # - skip lang packs that are already installed (obvious)
                for office in LibreOfficeS:
                    if office.version == latest_available_LO_version:
                        for lang in office.children:
                            if not lang.is_installed:
                                lang.allow_install()

            # b) newer version available - allow upgrading
            elif latest_available_LO_version == self._return_newer_ver(
                latest_available_LO_version,
                newest_installed_LO_version,
            ):
                log.debug(
                    "LibreOffice version available from the repo "
                    f"({latest_available_LO_version}) is newer then "
                    f"the installed one ({newest_installed_LO_version}) "
                )
                # newest LibreOffice installed can be removed
                # latest LibreOffice available can be installed
                # (older LibreOffice and OpenOffice versions
                #  can only be uninstalled).
                for office in LibreOfficeS:
                    if office.version == newest_installed_LO_version:
                        office.allow_removal()
                        for lang in office.children:
                            if not lang.is_installed:
                                lang.allow_removal()
                    if office.version == latest_available_LO_version:
                        office.allow_install()
                        for lang in office.children:
                            if not lang.is_installed:
                                lang.allow_install()

            # c) Something is wrong,
            else:
                log.error(
                    "Something is wrong. Installed LibreOffice version "
                    f"({newest_installed_LO_version}) is newer than the one "
                    f"in the repo ({latest_available_LO_version}). "
                    "This program will not allow you to make any changes."
                )
                for package in all_packages:
                    package.disallow_operations()

        # LibreOffice is not installed at all (OpenOffice may be present)
        else:
            log.debug("No installed LibreOffice found")
            # Allow for latest available LibreOffice to be installed
            for office in LibreOfficeS:
                if office.version == latest_available_LO_version:
                    office.allow_install()
                    for lang in office.children:
                        lang.allow_install()

        # 5) Check options for Clipart
        #
        # Clipart is installed
        if newest_installed_Clipart_version:
            # a) Installed Clipart already at latest version,
            if newest_installed_Clipart_version == latest_available_Clipart_version:
                log.debug("Clipart is already at latest available version")
            # b) Newer version available - allow upgrading
            elif latest_available_Clipart_version == self._return_newer_ver(
                latest_available_Clipart_version,
                newest_installed_Clipart_version,
            ):
                log.debug(
                    "Clipart version available from the repo "
                    f"({latest_available_Clipart_version}) is newer "
                    "then the installed one "
                    f"({newest_installed_Clipart_version})"
                )
                # newest Clipart installed can be removed
                # latest Clipart available can be installed
                for clipart in clipartS:
                    if clipart.version == newest_installed_Clipart_version:
                        clipart.allow_removal()
                    if clipart.version == latest_available_Clipart_version:
                        clipart.allow_install()
            # c) Something is wrong,
            else:
                log.error(
                    "Something is wrong. Installed Openclipart version "
                    f"({newest_installed_Clipart_version}) is newer than "
                    f"the one in the repo({latest_available_Clipart_version}). "
                    "This program will not allow you to make any changes."
                )
                for package in all_packages:
                    package.disallow_operations()

        # Clipart is not installed at all
        else:
            log.debug("No installed Clipart library found")
            # Allow for latest available Clipart to be installed
            for clipart in clipartS:
                if clipart.version == latest_available_Clipart_version:
                    clipart.allow_install()

        # If some operations are not permited because
        # of the system state not allowing for it
        # block them here
        block_any_install = (
            True
            if (
                self.global_flags.block_network_install
                or self.global_flags.block_local_copy_install
            )
            else False
        )
        block_removal = True if self.global_flags.block_removal else False

        for package in all_packages:
            if block_any_install:
                package.is_install_opt_enabled = False
            if block_removal:
                package.is_remove_opt_enabled = False

        return (
            latest_available_Java_version,
            newest_installed_Java_version,
            latest_available_LO_version,
            newest_installed_LO_version,
            latest_available_Clipart_version,
            newest_installed_Clipart_version,
        )

    def _return_newer_ver(self, v1: str, v2: str) -> str:
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

    def _get_available_software(self):
        available_virtual_packages = []

        java_ver = configuration.latest_available_java_version
        java_core_vp = VirtualPackage("core-packages", "Java", java_ver)
        java_core_vp.is_installed = False
        java_core_vp.real_files = [
            {
                "name": "task-java-2019-1pclos2019.noarch.rpm",
                "base_url": configuration.PCLOS_repo_base_url
                + configuration.PCLOS_repo_path,
                "estimated_download_size": 2,  # size in kilobytes
                "checksum": "",
            },
            {
                "name": "java-sun-16-2pclos2021.x86_64.rpm",
                "base_url": configuration.PCLOS_repo_base_url
                + configuration.PCLOS_repo_path,
                "estimated_download_size": 116736,  # size in kilobytes
                "checksum": "",
            },
        ]
        available_virtual_packages.append(java_core_vp)

        LO_ver = configuration.latest_available_LO_version
        LO_minor_ver = configuration.latest_available_LO_minor_version
        office_core_vp = VirtualPackage("core-packages", "LibreOffice", LO_ver)
        office_core_vp.is_installed = False
        office_core_vp.real_files = [
            {
                "name": "LibreOffice_" + LO_minor_ver + "_Linux_x86-64_rpm.tar.gz",
                "base_url": configuration.DocFund_base_url
                + LO_minor_ver
                + configuration.DocFund_path_ending,
                "estimated_download_size": 229376,  # size in kilobytes
                "checksum": "md5",
            },
        ]
        available_virtual_packages.append(office_core_vp)
        for lang in configuration.LO_supported_langs:
            office_lang_vp = VirtualPackage(lang, "LibreOffice", LO_ver)
            office_lang_vp.is_installed = False
            office_lang_vp.real_files = [
                {
                    "name": "LibreOffice_"
                    + LO_minor_ver
                    + "_Linux_x86-64_rpm_helppack_"
                    + lang
                    + ".tar.gz",
                    "base_url": configuration.DocFund_base_url
                    + LO_minor_ver
                    + configuration.DocFund_path_ending,
                    "estimated_download_size": 3277,  # size in kilobytes
                    "checksum": "md5",
                },
                {
                    "name": "LibreOffice_"
                    + LO_minor_ver
                    + "_Linux_x86-64_rpm_langpack_"
                    + lang
                    + ".tar.gz",
                    "base_url": configuration.DocFund_base_url
                    + LO_minor_ver
                    + configuration.DocFund_path_ending,
                    "estimated_download_size": 17408,  # size in kilobytes
                    "checksum": "md5",
                },
            ]
            available_virtual_packages.append(office_lang_vp)
        clipart_ver = configuration.latest_available_clipart_version
        clipart_core_vp = VirtualPackage("core-packages", "Clipart", clipart_ver)
        clipart_core_vp.is_installed = False
        clipart_core_vp.real_files = [
            {
                "name": "libreoffice-openclipart-"
                + clipart_ver
                + "-1pclos2023.x86_64.rpm",
                "base_url": configuration.PCLOS_repo_base_url
                + configuration.PCLOS_repo_path,
                "estimated_download_size": 8704,  # size in kilobytes
                "checksum": "",
            },
            {
                "name": "clipart-openclipart-2.0-1pclos2021.x86_64.rpm",
                "base_url": configuration.PCLOS_repo_base_url
                + configuration.PCLOS_repo_path,
                "estimated_download_size": 877568,  # size in kilobytes
                "checksum": "",
            },
        ]
        available_virtual_packages.append(clipart_core_vp)

        log.debug(f">>PRETENDING<< available software:")
        for p in available_virtual_packages:
            log.debug(f"                                 *  {p}")
        return available_virtual_packages

    def _detect_installed_software(self):
        installed_virtual_packages = []

        is_java_installed, java_ver = PCLOS.detect_installed_java()
        if is_java_installed:
            java_core_package = VirtualPackage("core-packages", "Java", java_ver)
            java_core_package.is_installed = True
            installed_virtual_packages.append(java_core_package)

        found_office_software = PCLOS.detect_installed_office_software()
        for suit in found_office_software:
            family = suit[0]
            version = suit[1]
            office_core_package = VirtualPackage(
                "core-packages",
                family,
                version,
            )
            office_core_package.is_installed = True
            installed_virtual_packages.append(office_core_package)
            for lang in suit[2]:
                office_lang_package = VirtualPackage(lang, family, version)
                office_lang_package.is_installed = True
                installed_virtual_packages.append(office_lang_package)

        is_clipart_installed, clipart_ver = PCLOS.detect_installed_clipart()
        if is_clipart_installed:
            clipart_core_package = VirtualPackage(
                "core-packages", "Clipart", clipart_ver
            )
            clipart_core_package.is_installed = True
            installed_virtual_packages.append(clipart_core_package)

        log.debug(f">>PRETENDING<< found_software:")
        for p in installed_virtual_packages:
            log.debug(f"                             *  {p}")
        return installed_virtual_packages

    def _flags_logic(self) -> tuple[bool, list[str]]:
        """'Rises' flags indicating some operations will not be available

        This method performs checks of the operating system and
        sets the status of the flags in the self._flags object
        to TRUE if some package operations need to be BLOCKED.

        Returns
        -------
        tuple
          (any_limitations: bool, info_list: list of strings)
          any_limitations is True if ANY flag was raised
          list contain human readable reason(s) for rising them.
        """

        # TODO: Add logging
        any_limitations = False
        info_list = []

        running_managers = PCLOS.get_running_package_managers()
        if running_managers:  # at least 1 package manager is running
            self.global_flags.block_removal = True
            self.global_flags.block_network_install = True
            self.global_flags.block_local_copy_install = True
            self.global_flags.block_checking_4_updates = True
            any_limitations = True
            msg = (
                "Some package managers are still running and "
                "as a result you won't be able to install or uninstall "
                "any packages. "
                "Close the managers listed and restart this program.\n"
                "manager: PID\n"
            )
            for manager, pid in running_managers.items():
                msg = msg + manager + ": " + pid + "  "
            info_list.append(msg)

        running_office_suits = PCLOS.get_running_Office_processes()
        if running_office_suits:  # an office app is running
            self.global_flags.block_removal = True
            self.global_flags.block_network_install = True
            self.global_flags.block_local_copy_install = True
            any_limitations = True
            msg = (
                "Office is running and as a result you "
                "won't be able to install or uninstall "
                "any packages."
                "Save your work, close Office and restart "
                "this program.\n"
                "Office: PID\n"
            )
            for office, pid in running_office_suits.items():
                msg = msg + office + ": " + pid + "  "
            info_list.append(msg)

        # no running manager prevents access to system rpm database
        if self.global_flags.block_checking_4_updates is False:
            (
                check_successfull,
                is_updated,
                explanation,
            ) = PCLOS.get_system_update_status()
            if check_successfull:
                if not is_updated:
                    self.global_flags.block_network_install = True
                    any_limitations = True
                    msg = (
                        "The OS is not fully updated "
                        "and as a result installations are blocked. "
                        "Update your system and restart "
                        "this program."
                    )
                    info_list.append(msg)
            else:
                self.global_flags.block_network_install = True
                any_limitations = True
                msg = (
                    "Failed to check update status \n"
                    "and as a result you won't be able to install "
                    "LibreOffice packages. "
                    "Check you internet connection "
                    "and restart this program."
                )
                if explanation:
                    msg = msg + "\n" + explanation
                info_list.append(msg)

        if not PCLOS.is_lomanager2_latest(configuration.lomanger2_version):
            self.global_flags.block_network_install = True
            any_limitations = True
            msg = (
                "You are running outdated version of "
                "this program! "
                "As a result you won't be able to install "
                "any packages."
                "Update your system and restart "
                "this program."
            )
            info_list.append(msg)

        return (any_limitations, info_list)

    def _install(
        self,
        keep_packages,
        statusfunc,
        progress_description,
        progress_percentage,
        step,
    ) -> dict:
        # Take current state of package tree and create packages list
        virtual_packages = []
        self._package_tree.get_subtree(virtual_packages)
        virtual_packages.remove(self._package_tree)

        collected_files = {
            "files_to_install": {
                "Java": [],
                "LibreOffice-core": [],
                "LibreOffice-langs": [],
                "Clipart": [],
            },
        }

        packages_to_download = [p for p in virtual_packages if p.is_marked_for_download]
        # STEP
        # Some packages need to be downloaded
        if packages_to_download:
            step.start("Collecting packages...")

            # Run collect_packages procedure
            is_every_pkg_collected, msg, collected_files = self._collect_packages(
                packages_to_download,
                progress_description=progress_description,
                progress_percentage=progress_percentage,
            )

            if is_every_pkg_collected is False:
                return statusfunc(
                    isOK=False,
                    msg="Failed to download requested packages.\n" + msg,
                )
            else:
                step.end("...done collecting files")
        # No need to download anything - just uninstalling
        else:
            step.skip()

        # Uninstall/Upgrade/Install packages
        status = self._make_changes(
            virtual_packages,
            rpms_and_tgzs_to_use=collected_files,
            keep_packages=keep_packages,
            statusfunc=statusfunc,
            progress_description=progress_description,
            progress_percentage=progress_percentage,
            step=step,
        )
        return status

    def _make_changes(
        self,
        virtual_packages,
        rpms_and_tgzs_to_use,
        keep_packages,
        statusfunc,
        progress_description,
        progress_percentage,
        step,
    ):
        # At this point network_install and local_copy_install
        # procedures converge and thus use the same function

        # STEP
        # Check if there is enough disk space unpack and install
        # requested packages
        step.start("Checking free disk space...")
        # TODO: Implement
        # if not something(keep_packages, virtual_packages, downloaded_files)
        # then error
        step.end()

        # STEP
        step.start("Trying to stop LibreOffice quickstarter...")
        self._terminate_LO_quickstarter()
        step.end()

        # STEP
        # Java needs to be installed?
        if rpms_and_tgzs_to_use["files_to_install"]["Java"]:
            step.start("Installing Java...")

            is_installed, msg = self._install_Java(
                rpms_and_tgzs_to_use,
                progress_description,
                progress_percentage,
            )
            if is_installed is False:
                return statusfunc(
                    isOK=False,
                    msg="Failed to install Java.\n" + msg,
                )
            step.end("...done installing Java")
        # No Java install requested
        else:
            step.skip()

        # At this point everything that is needed is downloaded and verified,
        # also Java is installed (except in unlikely case in which the user
        # installs only the Openclipart).
        # We can remove old Office components (if there are any to remove)
        # in preparation for the install step.

        # STEP
        # Any Office components need to be removed?
        office_packages_to_remove = [
            p
            for p in virtual_packages
            if p.is_marked_for_removal
            and (p.family == "OpenOffice" or p.family == "LibreOffice")
        ]
        if office_packages_to_remove:
            step.start("Removing selected Office components...")

            is_removed, msg = self._uninstall_office_components(
                office_packages_to_remove,
                progress_description,
                progress_percentage,
            )

            # If the procedure failed completely (no packages got uninstalled)
            # there is no problem - system state has not changed.
            # If however it succeeded but only partially this is a problem
            # because current Office might have gotten corrupted and a new
            # one will not be installed. Recovery from such a condition is
            # likely to require manual user intervention - not good.
            # TODO: Can office_uninstall procedure be made to have dry-run option
            #       to make sure that uninstall is atomic (all or none)?
            if is_removed is False:
                return statusfunc(
                    isOK=False,
                    msg="Failed to remove Office components.\n" + msg,
                )
            step.end("...done removing selected Office components")
        # No Office packages marked for removal
        else:
            step.skip()

        # STEP
        # Any Office components need to be installed?
        if (
            rpms_and_tgzs_to_use["files_to_install"]["LibreOffice-core"]
            or rpms_and_tgzs_to_use["files_to_install"]["LibreOffice-langs"]
        ):
            step.start("Installing selected Office components...")

            office_install_status, msg = self._install_LibreOffice_components(
                rpms_and_tgzs_to_use,
                progress_description,
                progress_percentage,
            )

            if office_install_status is False:
                return statusfunc(
                    isOK=False,
                    msg="Failed to install Office components.\n" + msg,
                )
            step.end("...done installing selected Office components")
        # No Office packages marked for install
        else:
            step.skip()

        # STEP
        # Any Office base package was affected ?
        # TODO: Can this be done better ?
        #       Return something from steps above?
        if rpms_and_tgzs_to_use["files_to_install"]["LibreOffice-core"]:
            step.start("Running postintall procedures...")

            self._disable_LO_update_checks()
            self._add_templates_to_etcskel()

            step.end("...done running postintall procedures")
        else:
            step.skip()

        # STEP
        for package in office_packages_to_remove:
            if (
                package.kind == "core-packages"
                and package.family == "LibreOffice"
                and package.is_marked_for_removal
            ):
                step.start("Changing file association...")

                self._clean_dot_desktop_files()

                step.end("...done")
            else:
                step.skip()

        # STEP
        # Clipart library is to be removed?
        clipart_packages_to_remove = [
            p
            for p in virtual_packages
            if p.family == "Clipart" and p.is_marked_for_removal
        ]
        if clipart_packages_to_remove:
            step.start("Removing Clipart library...")

            is_removed, msg = self._uninstall_clipart(
                clipart_packages_to_remove,
                progress_description,
                progress_percentage,
            )

            if is_removed is False:
                return statusfunc(
                    isOK=False,
                    msg="Failed to remove Clipart library.\n" + msg,
                )
            step.end("...done removing Clipart library")
        # Clipart was not marked for removal
        else:
            step.skip()

        # STEP
        # Clipart library is to be installed?
        if rpms_and_tgzs_to_use["files_to_install"]["Clipart"]:
            step.start("Installing Clipart library...")

            is_installed, msg = self._install_clipart(
                rpms_and_tgzs_to_use,
                progress_description,
                progress_percentage,
            )

            if is_installed is False:
                return statusfunc(
                    isOK=False,
                    msg="Failed to install Clipart library.\n" + msg,
                )
            step.end("...done installing Clipart library")
        # Clipart was not marked for install
        else:
            step.skip()

        # STEP
        # Should downloaded packages be kept ?
        if keep_packages is True:
            step.start("Saving packages...")

            is_saved, msg = self._save_copy_for_offline_install()
            if is_saved is False:
                return statusfunc(
                    isOK=False,
                    msg="Failed save packages.\n" + msg,
                )

            step.end("...done saving packages")
        else:
            step.skip()

        # STEP
        # clean up working directory and verified copies directory
        step.start("Removing temporary files and folders...")
        is_cleaned, msg = self._clean_directories()
        if is_cleaned is False:
            return statusfunc(
                isOK=False,
                msg="Failed to cleanup folders.\n" + msg,
            )
        step.end("...done removing temporary files and folders")

        status = {"is_OK": True, "explanation": ""}
        return status

    def _collect_packages(
        self,
        packages_to_download: list,
        progress_description,
        progress_percentage,
        skip_verify=False,
    ) -> tuple[bool, str, dict]:
        rpms_and_tgzs_to_use = {
            "files_to_install": {
                "Java": [],
                "LibreOffice-core": [],
                "LibreOffice-langs": [],
                "Clipart": [],
            },
        }

        log.debug(f"Packages to download:")
        for p in packages_to_download:
            log.debug(f"                    * {p}")

        # Check if there is connection to the server(s)
        # and requested files exist.
        # If so calculate/estimate the total download size
        total_download_size = 0
        for package in packages_to_download:
            for file in package.real_files:
                url = file["base_url"] + file["name"]
                try:
                    resp = urllib.request.urlopen(url)
                except urllib.error.HTTPError as error:
                    msg = f"While trying to open {url} an error occurred: "
                    msg = msg + f"HTTP error {error.code}: {error.reason}"
                    return (False, msg, rpms_and_tgzs_to_use)
                except urllib.error.URLError as error:
                    msg = f"While trying to open {url} an error occurred: "
                    msg = msg + f"{error.reason}"
                    return (False, msg, rpms_and_tgzs_to_use)
                else:
                    content_length = resp.info()["Content-Length"]
                    if content_length is not None and content_length != "0":
                        size = int(int(content_length) / 1024)
                        total_download_size += size
                    else:
                        total_download_size += file["estimated_size"]

        free_space = PCLOS.free_space_in_dir(configuration.working_dir)

        if free_space < total_download_size:
            msg = "Insufficient disk space to download packages"
            return (False, msg, rpms_and_tgzs_to_use)

        for package in packages_to_download:
            for file in package.real_files:
                f_url = file["base_url"] + file["name"]
                f_dest = configuration.working_dir.joinpath(file["name"])

                is_downloaded, error_msg = PCLOS.download_file(
                    f_url,
                    f_dest,
                    progress_percentage,
                    progress_description,
                )
                if not is_downloaded:
                    msg = f"Error while trying to download {f_url}: "
                    msg = msg + error_msg
                    return (False, msg, rpms_and_tgzs_to_use)

                if file["checksum"] and not skip_verify:
                    checksum_file = file["name"] + "." + file["checksum"]
                    csf_url = file["base_url"] + checksum_file
                    csf_dest = configuration.working_dir.joinpath(checksum_file)

                    is_downloaded, error_msg = PCLOS.download_file(
                        csf_url,
                        csf_dest,
                        progress_percentage,
                        progress_description,
                    )
                    if not is_downloaded:
                        msg = f"Error while trying to download {csf_url}: "
                        msg = msg + error_msg
                        return (False, msg, rpms_and_tgzs_to_use)

                    is_correct = PCLOS.verify_checksum(
                        f_dest, csf_dest, progress_percentage, progress_description
                    )
                    if not is_correct:
                        msg = f"Verification of the {file['name']} failed"
                        return (False, msg, rpms_and_tgzs_to_use)

                    if not PCLOS.remove_file(csf_dest):
                        msg = f"Error removing file {csf_dest}"
                        return (False, msg, rpms_and_tgzs_to_use)

                # Move file to verified files directory
                if package.family == "LibreOffice":
                    if package.is_langpack():
                        ending = "-langs"
                    else:
                        ending = "-core"
                    label = package.family + ending
                    folder_name = label + "_tgzs"
                else:
                    label = package.family
                    folder_name = label + "_rpms"
                f_verified = configuration.verified_dir.joinpath(folder_name)
                f_verified = f_verified.joinpath(file["name"])
                if not PCLOS.move_file(from_path=f_dest, to_path=f_verified):
                    msg = f"Error moving file {f_dest} to {f_verified}"
                    return (False, msg, rpms_and_tgzs_to_use)
                # Add file path to verified files list
                rpms_and_tgzs_to_use["files_to_install"][label].append(f_verified)

        log.debug(f"rpms_and_tgzs_to_use: {rpms_and_tgzs_to_use}")
        return (True, "", rpms_and_tgzs_to_use)

    def _terminate_LO_quickstarter(self):
        log.debug(">>PRETENDING<< Checking for LibreOffice quickstarter process...")
        log.debug(">>PRETENDING<< Terminating LibreOffice quickstarter...")
        time.sleep(2)
        log.debug(">>PRETENDING<< ...done.")

    def _install_Java(
        self,
        downloaded_files: dict,
        progress_description: Callable,
        progress_percentage: Callable,
    ) -> tuple[bool, str]:
        is_install_successful = False
        install_msg = ""

        log.debug(">>PRETENDING<< to be installing Java...")
        log.info("Starting Java install procedure...")
        if "files_to_install" in downloaded_files.keys():
            if rpms := downloaded_files["files_to_install"]["Java"]:
                log.debug(f"Java rpms to install {rpms}")
                progress_description("Installing java rpms ....")
                total_time_sek = 5
                steps = 30
                for i in range(steps):
                    progress = int((i / (steps - 1)) * 100)
                    progress_percentage(progress)
                    time.sleep(total_time_sek / steps)
                progress_description("...done installing java rpms")
                log.debug("...done")
                is_install_successful = True
                install_msg = ""
            else:
                is_install_successful = False
                install_msg = "Java install requested but list of files is empty."
                log.error(install_msg)
        else:
            is_install_successful = False
            install_msg = "Java install requested but no files_to_install dict passed."
            log.error(install_msg)

        is_install_successful = True
        log.info("Java successfully installed.")
        return (is_install_successful, install_msg)

    def _uninstall_office_components(
        self,
        packages_to_remove: list,
        progress_description: Callable,
        progress_percentage: Callable,
    ) -> tuple[bool, str]:
        is_uninstall_successful = False
        uninstall_msg = ""

        log.debug(f"Packages to remove:")
        for p in packages_to_remove:
            log.debug(f"                  * {p}")
        log.info(">>PRETENDING<< to be removing packages...")

        time.sleep(2)

        is_uninstall_successful = True
        log.info(">>PRETENDING<< ...done removing packages.")

        return (is_uninstall_successful, uninstall_msg)

    def _install_LibreOffice_components(
        self,
        downloaded_files: dict,
        progress_description: Callable,
        progress_percentage: Callable,
    ) -> tuple[bool, str]:
        is_install_successful = False
        install_msg = ""

        # TODO: There should be a .tar.gz file(s) in downloaded_files
        #       Unziping it takes place in this function
        log.info(">>PRETENDING<< to be installing files...")

        total_time_sek = 5
        steps = 30
        for i in range(steps):
            progress = int((i / (steps - 1)) * 100)  # progress in % (0-100)
            progress_percentage(progress)
            time.sleep(total_time_sek / steps)

        is_install_successful = True
        log.info(">>PRETENDING<< ...done installing packages.")

        return (is_install_successful, install_msg)

    def _disable_LO_update_checks(self):
        log.debug(
            ">>PRETENDING<< Preventing LibreOffice from looking for updates on its own..."
        )
        time.sleep(1)
        log.debug(">>PRETENDING<< ...done.")

    def _add_templates_to_etcskel(self):
        # TODO: This function should put a file (smth.xcu) to /etc/skel
        #       in order to have LO properly set up for any new user
        #       accounts created in the OS
        log.debug(">>PRETENDING<< Adding files to /etc/skel ...")
        time.sleep(1)
        log.debug(">>PRETENDING<< ...done.")

    def _clean_dot_desktop_files(self):
        # TODO: This function should remove association between LibreOffice
        #       and Open Document file formats (odt, odf, etc.) from the
        #       global .desktop file (and user files too?)
        log.debug(">>PRETENDING<< Rebuilding menu entries...")
        time.sleep(1)
        log.debug(">>PRETENDING<< ...done.")

    def _uninstall_clipart(
        self,
        packages_to_remove: list,
        progress_description: Callable,
        progress_percentage: Callable,
    ) -> tuple[bool, str]:
        is_uninstall_successful = False
        uninstall_msg = ""

        log.debug(f"Packages to remove:")
        for p in packages_to_remove:
            log.debug(f"                  * {p}")
        log.info(">>PRETENDING<< to be removing packages...")

        time.sleep(2)

        is_uninstall_successful = True
        log.info(">>PRETENDING<< ...done removing packages.")

        return (is_uninstall_successful, uninstall_msg)

    def _install_clipart(
        self,
        downloaded_files: dict,
        progress_description: Callable,
        progress_percentage: Callable,
    ) -> tuple[bool, str]:
        is_install_successful = False
        install_msg = ""

        log.info(">>PRETENDING<< to be installing files...")

        total_time_sek = 5
        steps = 30
        for i in range(steps):
            progress = int((i / (steps - 1)) * 100)  # progress in % (0-100)
            progress_percentage(progress)
            time.sleep(total_time_sek / steps)

        is_install_successful = True
        log.info(">>PRETENDING<< ...done installing packages.")

        return (is_install_successful, install_msg)

    def _save_copy_for_offline_install(self) -> tuple[bool, str]:
        # TODO: This function should mv verified_copies folder
        #       to lomanager2_saved_packages
        #       Path for both of those should be defined in the configuration
        is_save_successful = False
        save_msg = ""

        log.debug(">>PRETENDING<< to be saving files for offline install...")
        time.sleep(1)
        log.debug(">>PRETENDING<< ...done.")
        return (is_save_successful, save_msg)

    def _clean_directories(self):
        # TODO: This function should remove the contetns of working dir
        #       and verified copies dir.
        is_cleanup_successful = False
        cleanup_msg = ""

        log.debug(">>PRETENDING<< Cleaning temporary files...")
        time.sleep(1)
        log.debug(">>PRETENDING<< ...done.")

        return (is_cleanup_successful, cleanup_msg)

    def _local_copy_install_procedure(
        self,
        local_copy_directory,
        statusfunc,
        progress_description,
        progress_percentage,
        step,
    ) -> dict:
        is_modification_needed = False
        rpms_and_tgzs_to_use = {
            "files_to_install": {
                "Java": [],
                "LibreOffice-core": [],
                "LibreOffice-langs": [],
                "Clipart": [],
            },
        }

        # Take current state of package tree and create packages list
        virtual_packages = []
        self._package_tree.get_subtree(virtual_packages)
        virtual_packages.remove(self._package_tree)

        # local_copy_directory exists?
        if not pathlib.Path(local_copy_directory).is_dir():
            return statusfunc(
                isOK=False,
                msg="Could not find directory with saved packages.",
            )

        # STEP
        # Perform verification of local copy directory
        step.start("Scanning local copy directory for packages...")
        (
            Java_local_copy,
            LibreOffice_core_local_copy,
            LibreOffice_langs_local_copy,
            Clipart_local_copy,
        ) = self._verify_local_copy(local_copy_directory)
        step.end("...finished local copy directory scanning")

        # STEP
        step.start("Deciding what to install/remove...")
        # First, for every package, reset any 'request' flags that the user
        # may have set manually in the menu before changing mind and
        # choosing to install from local copy.
        # The logic of what should be installed/removed follows
        for package in virtual_packages:
            package.is_marked_for_removal = False
            package.is_marked_for_install = False
            package.is_marked_for_download = False

        if LibreOffice_core_local_copy["isPresent"]:
            # We are assuming the user wants to install it.
            # This is possible only if Java is present in the OS or
            # can be installed from local_copy_directory
            # TODO: change this to detect .is_installed flag of Java virtual
            #       package once it is guaranteed it can be found in virtual_packages
            if (
                PCLOS.is_java_installed() is False
                and Java_local_copy["isPresent"] is False
            ):
                return statusfunc(
                    isOK=False,
                    msg="Java is not installed in the system and was not "
                    "found in the directory provided.",
                )
            # TODO: change this to detect .is_installed flag of Java virtual
            #       package once it is guaranteed it can be found in virtual_packages
            elif (
                PCLOS.is_java_installed() is False
                and Java_local_copy["isPresent"] is True
            ):
                log.info("Java packages found will be installed.")
                rpms_and_tgzs_to_use["files_to_install"]["Java"] = Java_local_copy[
                    "rpm_abs_paths"
                ]
            elif (
                PCLOS.is_java_installed() is True
                and Java_local_copy["isPresent"] is False
            ):
                log.debug("Java already installed.")
            else:
                # TODO: Java is installed AND is present in local_copy_directory
                #       what should be done it such a case? Reinstall?
                #       Try using rpm -Uvh which will update it if package is newer?
                #       Skipping for now.
                pass

            # Reaching this point means Java is or will be installed
            log.info("LibreOffice packages found will be installed.")
            # No complex checks/comparisons for Office. To make sure
            # nothing gets messed up simply remove every Office package
            # that is installed.
            # (That includes OO, LO and any langpacks)
            log.debug("Marking ALL existing Office packages for removal.")
            for package in virtual_packages:
                if (
                    package.family == "OpenOffice"
                    or package.family == "LibreOffice"
                    and package.is_installed
                ):
                    package.is_marked_for_removal = True

            rpms_and_tgzs_to_use["files_to_install"][
                "LibreOffice-core"
            ] = LibreOffice_core_local_copy["tgz_abs_paths"]

            if LibreOffice_langs_local_copy["isPresent"]:
                # There are also some language packs that can be installed
                log.info("LibreOffice langpack(s) found will be installed too.")
                rpms_and_tgzs_to_use["files_to_install"][
                    "LibreOffice-langs"
                ] = LibreOffice_langs_local_copy["tgz_abs_paths"]

            # Signal that changes are needed
            is_modification_needed = is_modification_needed or True
        else:
            log.info(
                "LibreOffice core package wasn't found in the local copy "
                "directory and so LibreOffice will not be installed."
                "(LibreOffice langpacks or Java won't be installed "
                "either even if present in the local copy directory)."
            )
            is_modification_needed = is_modification_needed or False

        if Clipart_local_copy["isPresent"]:
            log.info("Openclipart packages found will be installed.")
            for package in virtual_packages:
                if package.family == "Clipart" and package.is_installed:
                    log.debug("Installed Clipart installation marked for removal")
                    # Clipart is already installed.
                    # Simply remove it and install the one from local copy
                    package.is_marked_for_removal = True

            rpms_and_tgzs_to_use["files_to_install"]["Clipart"] = Clipart_local_copy[
                "rpm_abs_paths"
            ]
            is_modification_needed = is_modification_needed or True
        else:
            log.info(
                "Openclipart packages were not found in the local copy "
                "directory so Openclipart will not be installed."
            )
            is_modification_needed = is_modification_needed or False
        step.end()

        if is_modification_needed is True:
            # Go ahead and make changes
            # (files provided by the user SHOULD NOT be removed - keep them)
            output = self._make_changes(
                virtual_packages,
                rpms_and_tgzs_to_use=rpms_and_tgzs_to_use,
                keep_packages=True,
                statusfunc=statusfunc,
                progress_description=progress_description,
                progress_percentage=progress_percentage,
                step=step,
            )
            return output
        else:
            return statusfunc(isOK=False, msg="Nothing to install. Check logs.")

    def _verify_local_copy(
        self,
        local_copy_directory: str,
    ) -> tuple:
        """Checks for presence of saved packages based on file name convention

        Based on expected files names this function checks
        the directory passed for the presence of:
            - 2 Java rpm packages (in Java_rpms subdir)
            - any LibreOffice core tar.gz archive
              (in LibreOffice-core_tgzs subdir)
            - LibreOffice langs/help tar.gz archives
              (in LibreOffice-langs_tgzs subdir)
            - 2 clipart rpm packages (in Clipart_rpms subdir)

        No specific LibreOffice version is enforced but version consistency
        among LibreOffice core and lang packages is checked.

        Returned is a tuple of dictionaries, each containing:
            - isPresent bool, signaling whether a component can be installed
            - rpm_abs_paths or tgz_abs_paths, list(s) of absolute paths to
              detected files

        Parameters
        ----------
        local_copy_directory : str
          Directory containing saved packages

        Returns
        -------
        tuple[dict,dict,dict,dict]
          for each component dict[bool, list]: T/F - can be installed
          list - absolute paths to detected files.
        """

        detected_core_ver = ""

        Java_local_copy = {"isPresent": False, "rpm_abs_paths": []}
        LibreOffice_core_local_copy = {"isPresent": False, "tgz_abs_paths": []}
        LibreOffice_langs_local_copy = {"isPresent": False, "tgz_abs_paths": []}
        Clipart_local_copy = {"isPresent": False, "rpm_abs_paths": []}

        # 1) Java rpms directory
        Java_dir = pathlib.Path(local_copy_directory).joinpath("Java_rpms")
        log.info(f"Checking {Java_dir}")
        if Java_dir.is_dir():
            # Search for: task-java-<something>.rpm ,  java-sun-<something>.rpm
            tj_regX = re.compile(
                r"^task-java-20[0-9][0-9]-[0-9]+pclos20[0-9][0-9]\.noarch\.rpm$"
            )
            js_regX = re.compile(
                r"^java-sun-(?P<ver_js>[0-9]+)-[0-9]+pclos20[0-9][0-9]\.x86_64\.rpm$"
            )
            task_java_files = []
            java_sun_files = []
            for file in Java_dir.iterdir():
                if match := tj_regX.search(file.name):
                    task_java_files.append(match.string)
                if match := js_regX.search(file.name):
                    java_sun_files.append(match.string)

            # Only when both files are present we can use them
            if task_java_files and java_sun_files:
                Java_local_copy["isPresent"] = True
                msg = ""
                for filename in task_java_files + java_sun_files:
                    msg = msg + filename + " "
                    abs_file_path = Java_dir.joinpath(filename)
                    Java_local_copy["rpm_abs_paths"].append(abs_file_path)
                log.info("Found Java rpm packages: " + msg)
            else:
                log.info("No usable Java rpm packages found")
        else:
            log.info("Java_rpms folder not found")

        # 2) LibreOffice core packages directory
        LO_core_dir = pathlib.Path(local_copy_directory)
        LO_core_dir = LO_core_dir.joinpath("LibreOffice-core_tgzs")
        log.info(f"Checking {LO_core_dir}")
        if LO_core_dir.is_dir():
            # Check for tar.gz archive with core packages
            regex_core = re.compile(
                r"^LibreOffice_(?P<ver_c>[0-9]*\.[0-9]*\.[0-9]*)_Linux_x86-64_rpm\.tar\.gz$"
            )
            LO_core_tgzs = []
            for file in LO_core_dir.iterdir():
                if match := regex_core.search(file.name):
                    LO_core_tgzs.append(match.string)
                    detected_core_ver = match.group("ver_c")
            if LO_core_tgzs:
                LibreOffice_core_local_copy["isPresent"] = True
                # In the unlikely situation of more then 1 matching files
                # pick only the first one.
                abs_file_path = LO_core_dir.joinpath(LO_core_tgzs[0])
                LibreOffice_core_local_copy["tgz_abs_paths"].append(abs_file_path)
                log.info("Found LibreOffice archive: " + LO_core_tgzs[0])
            else:
                log.info("No usable LibreOffice archive found")
        else:
            log.info("LibreOffice-core_tgzs folder not found")

        # 3) LibreOffice lang and help packages directory
        #    (its content is not critical for the decision procedure
        #     so just check if it exists and is non empty)
        LO_lang_dir = pathlib.Path(local_copy_directory)
        LO_lang_dir = LO_lang_dir.joinpath("LibreOffice-langs_tgzs")
        log.info(f"Checking {LO_lang_dir}")
        if LO_lang_dir.is_dir():
            # Check for any tar.gz archives with lang and help packages
            regex_lang = re.compile(
                r"^LibreOffice_(?P<ver_l>[0-9]*\.[0-9]*\.[0-9]*)_Linux_x86-64_rpm_langpack_[a-z]+-*\w*\.tar\.gz$"
            )
            regex_help = re.compile(
                r"^LibreOffice_(?P<ver_h>[0-9]*\.[0-9]*\.[0-9]*)_Linux_x86-64_rpm_helppack_[a-z]+-*\w*\.tar\.gz$"
            )
            LO_lang_tgzs = []
            ver_langs = []
            LO_help_tgzs = []
            ver_helps = []
            for file in LO_lang_dir.iterdir():
                if match_l := regex_lang.search(file.name):
                    LO_lang_tgzs.append(match_l.string)
                    ver_langs.append(match_l.group("ver_l"))
                if match_h := regex_help.search(file.name):
                    LO_help_tgzs.append(match_h.string)
                    ver_helps.append(match_h.group("ver_h"))

            def all_versions_the_same(items):
                return all(x == items[0] for x in items)

            # Only langpacks are required
            # (helppacks don't exist at all for some languages)
            # (Condition when a helppack exists without matching langpack
            #  is not checked - don't do it guys)
            if LO_lang_tgzs:
                if all_versions_the_same(ver_langs + ver_helps):
                    msg = ""
                    for filename in LO_lang_tgzs + LO_help_tgzs:
                        msg = msg + filename + " "
                    # Do additional check to see if lang packs match core pack
                    if LibreOffice_core_local_copy["isPresent"]:
                        if ver_langs[0] == detected_core_ver:
                            LibreOffice_langs_local_copy["isPresent"] = True
                            for filename in LO_lang_tgzs + LO_help_tgzs:
                                abs_file_path = LO_lang_dir.joinpath(filename)
                                LibreOffice_langs_local_copy["tgz_abs_paths"].append(
                                    abs_file_path
                                )
                            log.info("LibreOffice lang and helppacks found: " + msg)
                        else:
                            log.warning(
                                "LibreOffice langpack(s) found in the local "
                                "copy directory but their version does not "
                                "match LibreOffice core packages version. "
                                "Langpack(s) will not be installed."
                                "Found: " + msg
                            )
                    else:
                        log.info(
                            "LibreOffice lang and helppacks found "
                            "but LibreOffice core was not found. "
                            "Installation of just the lang/helppacks is not "
                            "supported. Lang and helppacks found: " + msg
                        )
                else:
                    log.warning(
                        "Found lang and helppacks have inconsistent "
                        "versions and will not be used."
                    )
            else:
                log.info("No usable lang or helppacks found")
        else:
            log.warning("LibreOffice-langs_tgzs folder not found")

        # 4) Clipart directory
        Clipart_dir = pathlib.Path(local_copy_directory)
        Clipart_dir = Clipart_dir.joinpath("Clipart_rpms")
        log.info(f"Checking {Clipart_dir}")
        if Clipart_dir.is_dir():
            # Search for: libreoffice-openclipart-<something>.rpm ,
            # clipart-openclipart-<something>.rpm
            ca_regeX = re.compile(
                r"^clipart-openclipart-(?P<ver_ca>[0-9]+\.[0-9]+)-[0-9]+pclos20[0-9][0-9]\.x86_64\.rpm$"
            )
            lca_regeX = re.compile(
                r"^libreoffice-openclipart-(?P<ver_lca>[0-9]+\.[0-9]+)-[0-9]+pclos20[0-9][0-9]\.x86_64\.rpm$"
            )

            openclipart_files = []
            lo_clipart_files = []
            for file in Clipart_dir.iterdir():
                if match := ca_regeX.search(file.name):
                    openclipart_files.append(match.string)
                if match := lca_regeX.search(file.name):
                    lo_clipart_files.append(match.string)

            # Only when both files are present we can use them
            if lo_clipart_files and openclipart_files:
                Clipart_local_copy["isPresent"] = True
                msg = ""
                for filename in lo_clipart_files + openclipart_files:
                    msg = msg + filename + " "
                    abs_file_path = Java_dir.joinpath(filename)
                    Clipart_local_copy["rpm_abs_paths"].append(abs_file_path)
                log.info("Found Openclipart rpm packages: " + msg)
            else:
                log.info("No usable Openclipart rpm packages found")
        else:
            log.warning("Clipart_rpms folder not found")

        log.debug(f"Java is present: {Java_local_copy['isPresent']}")
        log.debug(f"LO core is present: {LibreOffice_core_local_copy['isPresent']}")
        log.debug(f"LO langs is present: {LibreOffice_langs_local_copy['isPresent']}")
        log.debug(f"Clipart lib is present: {Clipart_local_copy['isPresent']}")
        return (
            Java_local_copy,
            LibreOffice_core_local_copy,
            LibreOffice_langs_local_copy,
            Clipart_local_copy,
        )

    # -- end Private methods of MainLogic


class ManualSelectionLogic(object):
    def __init__(
        self,
        root_node: VirtualPackage,
        latest_Java: str,
        newest_Java: str,
        latest_LO: str,
        newest_LO: str,
        latest_Clip: str,
        newest_Clip: str,
    ) -> None:
        # TODO: Refactor these variables. In fact there is no need
        #       to make any intermediate ones, just name the
        #       arguments properly and get rid of "self."
        self.latest_available_LO_version = latest_LO
        self.latest_available_clipart_version = latest_Clip
        self.newest_installed_LO_version = newest_LO

        # Object representing items in the menu
        self.root = root_node
        self.java = [c for c in self.root.children if "Java" in c.family][0]

        # useful at times
        self.packages = []
        self.root.get_subtree(self.packages)
        self.packages.remove(self.root)

        # A dictionary of packages to alter
        self.package_delta = {
            "packages_to_remove": [],
            "space_to_be_freed": 0,
            "packages_to_install": [],
            "space_to_be_used": 0,
        }

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
            # Notion of upgrade logic is deprecated
            return (False, False, False)
        elif column == 5:
            return (
                package.is_marked_for_install,
                package.is_install_opt_visible,
                package.is_install_opt_enabled,
            )
        elif column == 6:
            return (
                package.is_installed,
                True,
                True,
            )
        elif column == 7:
            return (
                package.is_marked_for_download,
                True,
                True,
            )
        else:
            return (None, None, None)

    def set_package_field(self, row: int, column: int, value: bool) -> bool:
        """Sets (marked for ...) flags for package applying dependencies logic

        Parameters
        ----------
        row : int
          Selected package as row in the package menu

        column : int
          Selected flag as column

        value : bool
          Requested flag value: True - mark, False - unmark

        Returns
        -------
        bool
          Request succeeded True/False
        """

        is_logic_applied = False
        package = self.packages[row]

        if column == 3:
            is_logic_applied = self._apply_removal_logic(package, value)
        elif column == 4:
            # Notion of upgrade logic is deprecated
            # return False
            is_logic_applied = False
        elif column == 5:
            is_logic_applied = self._apply_install_logic(package, value)
        else:
            is_logic_applied = False

        # Build the list of rpm to install/remove
        # # wipe previous delta
        self.package_delta["packages_to_remove"] = []
        self.package_delta["space_to_be_freed"] = 0
        self.package_delta["packages_to_install"] = []
        self.package_delta["space_to_be_used"] = 0
        # # create new delta
        for package in self.packages:
            if package.is_marked_for_removal or package.is_marked_for_upgrade:
                size = 0
                for file in package.real_files:
                    size += file["estimated_download_size"]
                    self.package_delta["packages_to_remove"] += [file["name"]]
                self.package_delta["space_to_be_freed"] = size
            if package.is_marked_for_install:
                size = 0
                for file in package.real_files:
                    size += file["estimated_download_size"]
                    self.package_delta["packages_to_install"] += [file["name"]]
                self.package_delta["space_to_be_used"] = size

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
        return 8

    # Private methods
    def _apply_install_logic(self, package: VirtualPackage, mark: bool):
        """Marks package for install changing flags of other packages accordingly

        This procedure will mark requested package for install and make
        sure this causes other packages to be also installed or prevented
        from being removed respecting dependencies.

        Parameters
        ----------
        package : VirtualPackage

        mark : bool
          True - mark for installed, False - unmark (give up installing)

        Returns
        -------
        bool
          True if packages install logic was applied successfully,
          False otherwise
        """

        log.debug(">>> Install logic triggerd <<<")

        is_apply_install_successul = False

        # OpenOffice dependency tree
        # OpenOffice cannot be installed, it can only be uninstalled
        # and is always marked for removal if detected.

        # LibreOffice dependency tree
        if package.family == "LibreOffice":
            # unmarking the request for install
            if mark is False:
                # 1) unmark yourself
                package.is_marked_for_install = False
                # 2) If this is the request to unmark the last of all
                #    new lang packs marked for install (user changes mind
                #    and decides not to install any new languages) -
                #    allow to uninstall the existing (if any) core-packages.
                if package.is_langpack():
                    syblings = package.get_syblings()
                    is_any_sybling_marked_for_install = any(
                        [s for s in syblings if s.is_marked_for_install]
                    )
                    if (
                        not is_any_sybling_marked_for_install
                        and package.parent is not None
                        and package.parent.is_installed
                    ):
                        package.parent.is_remove_opt_enabled = True
                # 3) If this IS the core-packages
                #    don't leave your lang packs hanging - unmark them
                if package.is_corepack():
                    for lang in package.children:
                        lang.is_marked_for_install = False
                # 4) if unmarking the last LO package of
                #    the latest available version
                #    make the removal option for installed Office
                #    accessible again
                if package.version == self.latest_available_LO_version:
                    family_members = package.get_your_family()
                    is_any_member_marked_for_install = any(
                        [m for m in family_members if m.is_marked_for_install]
                    )
                    if not is_any_member_marked_for_install:
                        for office in self.java.children:
                            if office.version != self.latest_available_LO_version:
                                office.is_remove_opt_enabled = True
                                for lang in office.children:
                                    lang.is_remove_opt_enabled = True
                is_apply_install_successul = True

            # requesting install
            if mark is True:
                # 1) mark yourself for install
                package.is_marked_for_install = True
                # 2) Java not installed - install it
                if not self.java.is_installed:
                    self.java.is_marked_for_install = True
                # 3) if installing latest LO mark older versions for removal
                if package.version == self.latest_available_LO_version:
                    for office in self.java.children:
                        if office.version != self.latest_available_LO_version:
                            office.mark_for_removal()
                            office.is_remove_opt_enabled = False
                            for lang in office.children:
                                lang.mark_for_removal()
                                lang.is_remove_opt_enabled = False
                # 4) If this is a lang pack
                if package.is_langpack():
                    if package.parent is not None:
                        if package.parent.is_installed:
                            # prevent installed parent getting removed
                            package.parent.is_remove_opt_enabled = False
                        else:
                            # parent not installed - install it as well
                            package.parent.is_marked_for_install = True
                # TODO: Possible not true anymore
                #     As the install option is only available
                #     when no installed LO was detected
                #     and thus the latest LO was added to self.packages
                #     there is no need to care about other installed LO suits
                #     Such situation should never occur.
                is_apply_install_successul = True

        # Clipart dependency tree
        if package.family == "Clipart":
            # As this is an independent package no special logic is needed,
            # just mark the package as requested.
            package.is_marked_for_install = mark
            is_apply_install_successul = True

        self._decide_what_to_download()
        return is_apply_install_successul

    def _apply_removal_logic(self, package: VirtualPackage, mark: bool) -> bool:
        """Marks package for removal changing flags of other packages accordingly

        This procedure will mark requested package for removal and make
        sure this causes other packages to be also removed or prevented
        from removal respecting dependencies.

        Parameters
        ----------
        package : VirtualPackage

        mark : bool
          True - mark for removal, False - unmark (give up removing)

        Returns
        -------
        bool
          True if packages removal logic was applied successfully,
          False otherwise
        """
        log.debug(">>> Removal logic triggerd <<<")

        is_apply_removal_successul = False

        # OpenOffice dependency tree
        # OpenOffice cannot be installed, it can only be uninstalled
        # and is always marked for removal if detected.

        # LibreOffice dependency tree
        if package.family == "LibreOffice":
            # unmarking the request for removal
            if mark is False:
                # unmark yourself from removal
                package.is_marked_for_removal = False
                # unmark the removal of an LibreOffice
                # - Do not orphan lang packs
                # - install option for new lang packs should re-enabled
                if package.is_corepack():
                    for lang in package.children:
                        lang.is_marked_for_removal = False
                        if not lang.is_installed:
                            lang.is_install_opt_enabled = True
                is_apply_removal_successul = True

            # requesting removal
            if mark is True:
                # mark yourself for removal
                package.is_marked_for_removal = True
                if package.is_corepack():
                    #  mark all your lang packages for removal too
                    for lang in package.children:
                        if lang.is_installed:
                            lang.is_marked_for_removal = True
                        # prevent installation of any new lang packs
                        else:
                            lang.is_install_opt_enabled = False
                            lang.is_marked_for_install = False
                is_apply_removal_successul = True

        # Clipart dependency tree
        if package.family == "Clipart":
            # As this is an independent package no special logic is needed,
            # just mark the package as requested.
            package.is_marked_for_removal = mark
            is_apply_removal_successul = True

        self._decide_what_to_download()
        return is_apply_removal_successul

    def _decide_what_to_download(self):
        for package in self.packages:
            # if package.is_marked_for_install and package.is_installed is False:
            if package.is_marked_for_install and package.is_installed is False:
                package.is_marked_for_download = True
            else:
                package.is_marked_for_download = False
