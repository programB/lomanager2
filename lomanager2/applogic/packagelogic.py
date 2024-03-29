"""
Copyright (C) 2023 programB

This file is part of lomanager2.

lomanager2 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3
as published by the Free Software Foundation.

lomanager2 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with lomanager2.  If not, see <http://www.gnu.org/licenses/>.
"""
import copy
import logging
import os
import pathlib
import re
import time
import xml.etree.ElementTree as ET
from typing import Callable

import configuration

from i18n import _

from . import PCLOS, net
from .callbacks import UnifiedProgressReporter
from .datatypes import SignalFlags, VirtualPackage, compare_versions
from .manualselection import ManualSelectionLogic

log = logging.getLogger("lomanager2_logger")


class MainLogic(object):
    def __init__(self, skip_update_check: bool) -> None:
        self.skip_update_check = skip_update_check

        make_changes_count = 7
        self.normal_procedure_step_count = 3 + make_changes_count
        self.local_copy_procedure_step_count = 3 + make_changes_count
        self.rebuild_tree_procedure_step_count = 4
        self.check_system_procedure_step_count = (
            4 + self.rebuild_tree_procedure_step_count
        )

        self.rebuild_timestamp = 0
        self.warnings = []
        self.global_flags = SignalFlags()
        self.package_tree_root = VirtualPackage("master-node", "", "")

        self._package_menu = ManualSelectionLogic(
            self.package_tree_root, "", "", "", "", "", ""
        )

    # -- Public interface for MainLogic
    def change_removal_mark(self, package: VirtualPackage, mark: bool) -> bool:
        return self._package_menu.apply_removal_logic(package, mark)

    def change_install_mark(self, package: VirtualPackage, mark: bool) -> bool:
        return self._package_menu.apply_install_logic(package, mark)

    def get_warnings(self):
        warnings = copy.deepcopy(self.warnings)
        # clear warnings object
        self.warnings = []
        return warnings

    def inform_user(self, msg: str, explanation: str, isOK: bool):
        if isOK:
            log.info(msg + explanation)
        else:
            log.error(msg + explanation)
        # Do not add the same warning twice
        # (it will be logged in the code above as many times as sent)
        warning = (isOK, msg, explanation)
        if not warning in self.warnings:
            self.warnings.append(warning)

    def get_planned_changes(self):
        return (
            self._package_menu.info_to_install,
            self._package_menu.info_to_remove,
        )

    def apply_changes(self, *args, **kwargs):
        """Does the preparations and collects files before calling _make_changes

        This method does the final decision of what should be installed/removed
        and calls file download procedure if any files have to be collected.
        When done it calls _make_changes to do modify system state.
        """
        if self.global_flags.ready_to_apply_changes is False:
            msg = _("Not ready to apply changes")
            self.inform_user(msg, "", isOK=False)
            return

        if "keep_packages" in kwargs.keys():
            keep_packages = kwargs["keep_packages"]
        else:
            msg = _("keep_packages argument is obligatory")
            self.inform_user(msg, "", isOK=False)
            return

        if "force_java_download" in kwargs.keys():
            force_java_download = kwargs["force_java_download"]
        else:
            msg = _("force_java_download argument is obligatory")
            self.inform_user(msg, "", isOK=False)
            return

        # We are good to go
        progress_reporter = UnifiedProgressReporter(
            total_steps=self.normal_procedure_step_count, callbacks=kwargs
        )

        # Mark Java for download if the user requested that
        java_package = [
            c for c in self.package_tree_root.children if "Java" in c.family
        ][0]
        if force_java_download is True:
            java_package.is_marked_for_download = True
            # TODO: If force_java_download is set by the user it most likely
            #       means Java is already installed and only
            #       download is wanted. In that case java package definition
            #       from _get_available_software will not be used
            #       and real_files list will be empty. This causes crash
            #       in download in _collect_packages.
            #       Adding missing information here fixes the problem
            #       but this is hacky.
            java_package.real_files = [
                {
                    "name": "task-java-2019-1pclos2019.noarch.rpm",
                    "base_url": configuration.PCLOS_repo_base_url
                    + configuration.PCLOS_repo_path,
                    "estimated_download_size": 1592,  # size in bytes
                    "checksum": "",
                },
                {
                    "name": "java-sun-16-2pclos2021.x86_64.rpm",
                    "base_url": configuration.PCLOS_repo_base_url
                    + configuration.PCLOS_repo_path,
                    "estimated_download_size": 119920500,  # size in bytes
                    "checksum": "",
                },
            ]

        # Block any other calls of this function and proceed
        self.global_flags.ready_to_apply_changes = False

        log.info(_("*** Applying selected changes ***"))

        virtual_packages = []
        self.package_tree_root.get_subtree(virtual_packages)
        virtual_packages.remove(self.package_tree_root)

        collected_files = {
            "files_to_install": {
                "Java": [],
                "LibreOffice-core": [],
                "LibreOffice-langs": [],
                "Clipart": [],
            },
        }

        # STEP
        progress_reporter.step_start(_("Cleaning temporary directories"))
        is_cleaned_w, msg_w = PCLOS.clean_dir(configuration.working_dir)
        if is_cleaned_w is False:
            msg = _("Failed to (re)create working directory: ")
            self.inform_user(msg, msg_w, isOK=False)
            return
        is_cleaned_v, msg_v = PCLOS.clean_dir(configuration.verified_dir)
        if is_cleaned_v is False:
            msg = _("Failed to (re)create verified directory: ")
            self.inform_user(msg, msg_v, isOK=False)
            return
        else:
            directories = [
                configuration.working_dir,
                configuration.verified_dir.joinpath("Java_rpms"),
                configuration.verified_dir.joinpath("LibreOffice-core_tgzs"),
                configuration.verified_dir.joinpath("LibreOffice-langs_tgzs"),
                configuration.verified_dir.joinpath("Clipart_rpms"),
            ]
            for dir in directories:
                PCLOS.create_dir(dir)
        progress_reporter.step_end()

        packages_to_download = [p for p in virtual_packages if p.is_marked_for_download]
        if packages_to_download:
            # Some packages need to be downloaded
            # STEP
            progress_reporter.step_start(_("Checking free disk space for download"))
            is_enough, needed, available = self._space_for_download(
                packages_to_download
            )
            if is_enough is False:
                msg = _(
                    "Insufficient disk space to download selected "
                    "packages. Needed: {}. Available: {}"
                ).format(needed, available)
                self.inform_user(msg, "", isOK=False)
                return
            progress_reporter.step_end()

            # STEP
            progress_reporter.step_start(_("Collecting files"))
            is_every_pkg_collected, expl, collected_files = self._collect_packages(
                packages_to_download,
                progress_reporter=progress_reporter,
            )

            if is_every_pkg_collected is False:
                msg = _("Failed to download requested packages: ")
                self.inform_user(msg, expl, isOK=False)
                return
            else:
                progress_reporter.step_end()
        else:
            progress_reporter.step_skip(_("Nothing to download"))

        # Uninstall/Install packages
        self._make_changes(
            virtual_packages,
            rpms_and_tgzs_to_use=collected_files,
            create_offline_copy=keep_packages,
            progress_reporter=progress_reporter,
        )

    def install_from_local_copy(self, *args, **kwargs):
        """Applies local copy installation logic before calling _make_changes

        This method checks if the directory provided by the user contains
        files that can be used to install Java, LibreOffice or Clipart
        When done it calls _make_changes to do modify system state.
        """
        if self.global_flags.ready_to_apply_changes is False:
            msg = _("Not ready to apply changes")
            self.inform_user(msg, "", isOK=False)
            return

        if self.global_flags.block_local_copy_install is True:
            msg = _("Local copy installation was blocked")
            self.inform_user(msg, "", isOK=False)
            return

        if "local_copy_dir" in kwargs.keys():
            local_copy_directory = kwargs["local_copy_dir"]
        else:
            msg = _("local_copy_dir argument is obligatory")
            self.inform_user(msg, "", isOK=False)
            return

        # We are good to go
        progress_reporter = UnifiedProgressReporter(
            total_steps=self.local_copy_procedure_step_count, callbacks=kwargs
        )

        # Block any other calls of this function and proceed
        self.global_flags.ready_to_apply_changes = False

        log.info(_("*** Beginning local copy install procedure ***"))

        is_modification_needed = False
        rpms_and_tgzs_to_use = {
            "files_to_install": {
                "Java": [],
                "LibreOffice-core": [],
                "LibreOffice-langs": [],
                "Clipart": [],
            },
        }

        # STEP
        progress_reporter.step_start(_("Cleaning temporary directories"))
        is_wd_cleaned, msg_w = PCLOS.clean_dir(configuration.working_dir)
        if is_wd_cleaned is False:
            msg = _("Failed to (re)create working directory: ")
            self.inform_user(msg, msg_w, isOK=False)
            return
        is_vd_cleaned, msg_v = PCLOS.clean_dir(configuration.verified_dir)
        if is_vd_cleaned is False:
            msg = _("Failed to (re)create verified directory: ")
            self.inform_user(msg, msg_v, isOK=False)
            return
        else:
            directories = [
                configuration.working_dir,
                configuration.verified_dir.joinpath("Java_rpms"),
                configuration.verified_dir.joinpath("LibreOffice-core_tgzs"),
                configuration.verified_dir.joinpath("LibreOffice-langs_tgzs"),
                configuration.verified_dir.joinpath("Clipart_rpms"),
            ]
            for dir in directories:
                PCLOS.create_dir(dir)
        progress_reporter.step_end()

        # Take current state of package tree and create packages list
        virtual_packages = []
        self.package_tree_root.get_subtree(virtual_packages)
        virtual_packages.remove(self.package_tree_root)

        # Checks if local_copy_directory exists at all
        if not pathlib.Path(local_copy_directory).is_dir():
            msg = _("Could not find directory with saved packages")
            self.inform_user(msg, "", isOK=False)
            return

        # STEP
        progress_reporter.step_start(_("Scanning local copy directory for packages"))
        (
            Java_local_copy,
            LibreOffice_core_local_copy,
            LibreOffice_langs_local_copy,
            Clipart_local_copy,
        ) = self._verify_local_copy(local_copy_directory)
        progress_reporter.step_end()

        # STEP
        progress_reporter.step_start(_("Deciding what to install/remove"))
        # First, for every package, reset any 'request' flags that the user
        # may have set manually in the menu before changing mind and
        # choosing to install from local copy.
        # The logic of what should be installed/removed follows
        java = [c for c in self.package_tree_root.children if "Java" in c.family][0]
        for package in virtual_packages:
            package.is_marked_for_removal = False
            package.is_marked_for_install = False
            package.is_marked_for_download = False

        if LibreOffice_core_local_copy["isPresent"]:
            # We are assuming the user wants to install it.
            # This is possible only if Java is present in the OS or
            # can be installed from local_copy_directory
            if not java.is_installed and not Java_local_copy["isPresent"]:
                msg = _(
                    "Java is not installed in the system and was "
                    "not found in the directory provided"
                )
                self.inform_user(msg, "", isOK=False)
                return
            elif not java.is_installed and Java_local_copy["isPresent"]:
                log.info(_("Java packages found will be installed."))
                rpms_and_tgzs_to_use["files_to_install"]["Java"] = Java_local_copy[
                    "rpm_abs_paths"
                ]
            elif java.is_installed and not Java_local_copy["isPresent"]:
                log.debug(_("Java already installed."))
            else:
                log.debug(
                    _(
                        "Java was found in the local copy directory but "
                        "Java is already installed so it won't be reinstalled."
                    )
                )

            # Reaching this point means Java is or will be installed
            log.info(_("LibreOffice packages found will be installed."))

            # No complex checks/comparisons for Office. To make sure
            # nothing gets messed up simply remove every Office package
            # that is installed.
            # (That includes OO, LO and any langpacks)
            for package in virtual_packages:
                if (
                    package.family == "OpenOffice"
                    or package.family == "LibreOffice"
                    and package.is_installed
                ):
                    package.is_marked_for_removal = True
                    log.info(_("Package ({}) will be removed").format(package))

            # Add LibreOffice core packages and langpacks (if any)
            # to the list of files
            rpms_and_tgzs_to_use["files_to_install"][
                "LibreOffice-core"
            ] = LibreOffice_core_local_copy["tgz_abs_paths"]

            if LibreOffice_langs_local_copy["isPresent"]:
                log.info(_("Found LibreOffice langpack(s) will be installed."))
                rpms_and_tgzs_to_use["files_to_install"][
                    "LibreOffice-langs"
                ] = LibreOffice_langs_local_copy["tgz_abs_paths"]

            # Signal that changes are needed
            is_modification_needed = is_modification_needed or True
        else:
            log.info(
                _(
                    "LibreOffice core package wasn't found in the local copy "
                    "directory and so LibreOffice will not be installed. "
                    "(LibreOffice langpacks or Java won't be installed either "
                    "even if present in the local copy directory)."
                )
            )
            is_modification_needed = is_modification_needed or False

        if Clipart_local_copy["isPresent"]:
            log.info(_("Openclipart packages found will be installed."))
            for package in virtual_packages:
                if package.family == "Clipart" and package.is_installed:
                    log.debug(_("Installed Clipart installation marked for removal"))
                    # Clipart is already installed.
                    # Simply remove it and install the one from local copy
                    package.is_marked_for_removal = True

            rpms_and_tgzs_to_use["files_to_install"]["Clipart"] = Clipart_local_copy[
                "rpm_abs_paths"
            ]
            is_modification_needed = is_modification_needed or True
        else:
            log.info(
                _(
                    "Openclipart packages were not found in the local copy "
                    "directory so Openclipart will not be installed."
                )
            )
            is_modification_needed = is_modification_needed or False
        progress_reporter.step_end()

        if is_modification_needed is True:
            # Go ahead and make changes
            # (files provided by the user SHOULD NOT be removed
            #  - DO NOT overwrite them by creating an offline copy)
            self._make_changes(
                virtual_packages,
                rpms_and_tgzs_to_use=rpms_and_tgzs_to_use,
                create_offline_copy=False,
                progress_reporter=progress_reporter,
            )
        else:
            msg = _("Nothing to install. Check logs.")
            self.inform_user(msg, "", isOK=False)

    def check_system_state(self, *args, **kwargs):
        """Checks if installing/removing packages is allowed

        This method performs checks of the operating system and
        sets the status of the flags in the self.global_flags object
        to TRUE if some operations need to be BLOCKED.
        If this happens a human readable messages for the cause
        is added to the self.warnings list.
        """

        progress_reporter = UnifiedProgressReporter(
            total_steps=self.check_system_procedure_step_count, callbacks=kwargs
        )
        msg = ""

        log.info(_("*** Beginning system check procedure ***"))
        progress_reporter.step_start(_("Looking for running package managers"))
        status, running_managers = PCLOS.get_running_package_managers()
        if status is False:
            self.global_flags.block_removal = True
            self.global_flags.block_normal_install = True
            self.global_flags.block_local_copy_install = True
            self.global_flags.block_checking_4_updates = True
            msg = _("Unexpected error. Could not read processes PIDs. Check log.")
            self.inform_user(msg, "", isOK=False)
        if running_managers:  # at least 1 package manager is running
            self.global_flags.block_removal = True
            self.global_flags.block_normal_install = True
            self.global_flags.block_local_copy_install = True
            self.global_flags.block_checking_4_updates = True
            msg = _(
                "Some package managers are still running and as a result "
                "you won't be able to install or uninstall any packages. "
                "Close the managers listed and restart this "
                "program.\nmanager: PID\n"
            )
            for manager, pids in running_managers.items():
                msg += manager + ": " + str(pids) + "  "
            self.inform_user(msg, "", isOK=False)
        else:
            log.info(_("No running package manager found ...good"))
        progress_reporter.step_end()

        progress_reporter.step_start(_("Looking for running Office"))
        status, running_office_suits = PCLOS.get_running_Office_processes()
        if status is False:
            self.global_flags.block_removal = True
            self.global_flags.block_normal_install = True
            self.global_flags.block_local_copy_install = True
            msg = _("Unexpected error. Could not read processes PIDs. Check log.")
            self.inform_user(msg, "", isOK=False)
        if running_office_suits:  # an office app is running
            self.global_flags.block_removal = True
            self.global_flags.block_normal_install = True
            self.global_flags.block_local_copy_install = True
            msg = _(
                "Office is running and as a result you won't be able to "
                "install or uninstall any packages. Save your work, "
                "close Office and restart this program.\nOffice: PID\n"
            )
            for office, pids in running_office_suits.items():
                msg += office + ": " + str(pids) + "  "
            self.inform_user(msg, "", isOK=False)
        else:
            log.info(_("No running Office suits found ...good"))
        progress_reporter.step_end()

        if self.global_flags.block_checking_4_updates is False:
            # no running manager prevents access to system rpm database
            progress_reporter.step_start(_("Checking for system updates"))
            explanation = ""
            if self.skip_update_check:
                msg = _(
                    "Checking for OS updates was bypassed. Installing "
                    "packages in this mode can potentially mess up "
                    "your system! Use at your own risk."
                )
                (
                    check_successful,
                    is_updated,
                    explanation,
                ) = (True, True, "")
                self.inform_user(msg, "", isOK=False)
            else:
                (
                    check_successful,
                    is_updated,
                    explanation,
                ) = PCLOS.check_system_update_status()
            if check_successful:
                if not is_updated:
                    self.global_flags.block_normal_install = True
                    msg = _(
                        "The OS is not fully updated and as a result "
                        "installations are blocked. Update your system "
                        "and restart this program."
                    )
                    self.inform_user(msg, "", isOK=False)
                else:
                    log.info(_("System is fully updated ...good"))
            else:
                self.global_flags.block_normal_install = True
                msg = _(
                    "Failed to check update status \nand as a result you "
                    "won't be able to install LibreOffice packages. "
                    "Check your internet connection and restart this program."
                )
                self.inform_user(msg, explanation, isOK=False)
        else:
            log.warning(_("Update checking was blocked"))
        progress_reporter.step_end()

        for flag in vars(self.global_flags):
            log.debug(f"{flag}: {self.global_flags.__dict__[flag]}")

        progress_reporter.step_start(_("Checking if live session is active"))
        if PCLOS.is_live_session_active():
            msg = _(
                "OS is running in live session mode.\nAll modifications "
                "made will be lost on reboot unless you install the "
                "system on a permanent drive. Also note that in live "
                "session mode LibreOffice may fail to install due "
                "to insufficient virtual disk space."
            )
            self.inform_user(msg, "", isOK=False)
        else:
            log.info(_("Running on installed system ...good"))
        progress_reporter.step_end()

        self.rebuild_package_tree(progress_reporter, *args, **kwargs)

    def rebuild_package_tree(self, progress_reporter=None, *args, **kwargs):
        """Replaces old package tree with new one with THE SAME root

        Called every time the state of the actually installed rpm packages
        in the OS changes. It detects installed software, creates a list
        of packages available for installation and using both builds a
        package dependency tree (dependencies are predetermined).
        It finishes by applying restriction to what can be installed/removed
        based on OS state.
        """
        if progress_reporter is None:
            progress_reporter = UnifiedProgressReporter(
                total_steps=self.rebuild_tree_procedure_step_count, callbacks=kwargs
            )
        msg = ""

        progress_reporter.step_start(_("Detecting installed software"))
        installed_vps = self._detect_installed_software()
        progress_reporter.step_end()

        progress_reporter.step_start(_("Building available software list"))
        (
            available_vps,
            recommended_Java_ver,
            recommended_LO_ver,
            recommended_Clip_ver,
        ) = self._get_available_software()
        progress_reporter.step_end()

        progress_reporter.step_start(_("Building dependency tree"))
        complement = [p for p in available_vps if p not in installed_vps]
        joint_package_list = installed_vps + complement
        self._build_dependency_tree(joint_package_list)
        log.debug(_("TREE \n") + self.package_tree_root.tree_representation())
        progress_reporter.step_end()

        progress_reporter.step_start(_("Applying restrictions"))
        (
            newest_Java_ver,
            newest_LO_ver,
            newest_Clip_ver,
        ) = self._set_packages_initial_state(
            recommended_Java_ver,
            recommended_LO_ver,
            recommended_Clip_ver,
        )
        progress_reporter.step_end()

        self._package_menu = ManualSelectionLogic(
            root_node=self.package_tree_root,
            latest_Java_version=recommended_Java_ver,
            newest_Java_version=newest_Java_ver,
            recommended_LO_version=recommended_LO_ver,
            newest_installed_LO_version=newest_LO_ver,
            recommended_Clipart_version=recommended_Clip_ver,
            newest_Clipart_version=newest_Clip_ver,
        )
        self.global_flags.ready_to_apply_changes = True
        self.rebuild_timestamp = time.time()
        if (
            configuration.force_specific_LO_version != ""
            and newest_LO_ver != ""
            and newest_LO_ver != configuration.force_specific_LO_version
        ):
            msg = _("Downgrade of LibreOffice to version {} is recommended.").format(
                configuration.force_specific_LO_version
            )
            self.inform_user(msg, "", isOK=False)

    def remove_temporary_dirs(self):
        log.debug(_("Removing temporary directory"))
        if PCLOS.force_rm_directory(configuration.temporary_dir):
            log.info(_("Temporary directories successfully removed"))
            return True
        else:
            msg = _("Error: Temporary directory {} couldn't be removed").format(
                configuration.temporary_dir
            )
            self.inform_user(msg, "", isOK=False)
            return False

    # -- end Public interface for MainLogic

    # -- Private methods of MainLogic
    def _build_dependency_tree(self, packageS: list[VirtualPackage]):
        # Make master node forget its children
        # (this will should delete all descendent virtual package objects)
        self.package_tree_root.children = []
        current_parent = self.package_tree_root

        # 1st tier: Link Java and Clipart to top level package
        already_handled = []
        for package in packageS:
            if package.family == "Clipart" and package.kind == "core-packages":
                current_parent.add_child(package)
                already_handled.append(package)
        # and remove from packageS list
        packageS = [p for p in packageS if p not in already_handled]
        # Warning: packageS now becomes and independent copy of original
        #          packageS passed in the argument so this selective
        #          copying is not removing items from the original list

        for package in packageS:
            if package.family == "Java" and package.kind == "core-packages":
                current_parent.add_child(package)
                already_handled.append(package)
                current_parent = package
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
        packageS = [p for p in packageS if p not in already_handled]

        # 3rd tier: Link OO and LO lang packages to their parent core packages
        for package in packageS:
            if package.kind != "core-packages":
                for matching_parent in Office_parents:
                    if matching_parent.version == package.version:
                        matching_parent.add_child(package)
                        already_handled.append(package)
        packageS = [p for p in packageS if p not in already_handled]
        # At this point packageS should be empty

    def _set_packages_initial_state(
        self,
        recommended_Java_version,
        recommended_LO_version,
        recommended_Clipart_version,
    ) -> tuple[str, str, str]:
        """Decides on initial conditions for packages install/removal."""
        root = self.package_tree_root

        # For each software component (Java, LibreOffice, Clipart) check:
        # - the newest installed version
        newest_installed_Java_version = ""
        java = [c for c in root.children if "Java" in c.family][0]
        if java.is_installed:
            newest_installed_Java_version = java.version
        # java install/remove options are never visible

        installed_LOs = [
            c for c in java.children if "LibreOffice" in c.family and c.is_installed
        ]
        if installed_LOs:
            newest_installed_LO_version = installed_LOs[0].version
            for office in installed_LOs:
                newest_installed_LO_version = (
                    office.version
                    if compare_versions(office.version, newest_installed_LO_version)
                    >= 1
                    else newest_installed_LO_version
                )
        else:
            newest_installed_LO_version = ""

        installed_clipartS = [
            c for c in root.children if "Clipart" in c.family and c.is_installed
        ]
        if installed_clipartS:
            newest_installed_Clipart_version = installed_clipartS[0].version
            for clipart in installed_clipartS:
                newest_installed_Clipart_version = (
                    clipart.version
                    if compare_versions(
                        clipart.version, newest_installed_Clipart_version
                    )
                    >= 1
                    else newest_installed_Clipart_version
                )
        else:
            newest_installed_Clipart_version = ""

        LibreOfficeS = [c for c in java.children if "LibreOffice" in c.family]
        clipartS = [c for c in root.children if "Clipart" in c.family]
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
        # Java removal (or upgrade to newer version) is not supported
        # by this program. This should be done by a proper package manager
        # like Synaptic
        if java.is_installed:
            java.is_marked_for_removal = False
            java.is_remove_opt_enabled = False
            java.is_remove_opt_visible = False

        # 4) Check options for LibreOffice
        # LibreOffice is installed?
        if newest_installed_LO_version:
            log.debug(_("Newest installed LO: {}").format(newest_installed_LO_version))

            # a) is recommended version already installed ?
            if newest_installed_LO_version == recommended_LO_version:
                log.debug(_("Recommended LibreOffice version is already installed"))
                # Allow for additional langpacks installation
                # - LibreOffice only !!! OpenOffice office is not supported.
                # - skip langpacks that are already installed
                for office in LibreOfficeS:
                    if office.version == recommended_LO_version:
                        for lang in office.children:
                            if not lang.is_installed:
                                lang.allow_install()

            # b) a different version is available - allow it to be installed
            #    (We don't care if this different version is newer or older
            #     than the one installed - what matters is that it's different.
            #     It is very unlikely that it will be older unless we are
            #     downgrading in which case this is what we actually want.)
            else:
                log.debug(
                    _(
                        "Recommended LibreOffice version ({}) is different "
                        "than the installed one ({})"
                    ).format(recommended_LO_version, newest_installed_LO_version)
                )
                # newest LibreOffice installed can be removed
                # recommended LibreOffice can be installed
                # (older LibreOffice and OpenOffice versions
                #  can only be uninstalled).
                for office in LibreOfficeS:
                    if office.version == newest_installed_LO_version:
                        office.allow_removal()
                        for lang in office.children:
                            if lang.is_installed:
                                lang.allow_removal()
                    if office.version == recommended_LO_version:
                        office.allow_install()
                        for lang in office.children:
                            if lang.is_installed is False:
                                lang.allow_install()

        else:
            log.debug(_("No installed LibreOffice found"))
            # Allow the recommended version to be installed
            for office in LibreOfficeS:
                if office.version == recommended_LO_version:
                    office.allow_install()
                    for lang in office.children:
                        lang.allow_install()

        # 5) Check options for Clipart
        # Clipart is installed
        if newest_installed_Clipart_version:
            if newest_installed_Clipart_version == recommended_Clipart_version:
                log.debug(_("Clipart is already at latest available version"))
            else:
                log.debug(
                    _(
                        "Recommended Clipart version ({}) is different "
                        "than the installed one ({})"
                    ).format(
                        recommended_Clipart_version, newest_installed_Clipart_version
                    )
                )
                # newest Clipart installed can be removed
                # latest Clipart available can be installed
                for clipart in clipartS:
                    if clipart.version == newest_installed_Clipart_version:
                        clipart.allow_removal()
                    if clipart.version == recommended_Clipart_version:
                        clipart.allow_install()

        else:
            log.debug(_("No installed Clipart library found"))
            # Allow the recommended version to be installed
            for clipart in clipartS:
                if clipart.version == recommended_Clipart_version:
                    clipart.allow_install()

        # If some operations are not permitted because
        # of the system state not allowing for it block them here
        block_any_install = (
            True
            if (
                self.global_flags.block_normal_install
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
            newest_installed_Java_version,
            newest_installed_LO_version,
            newest_installed_Clipart_version,
        )

    def _get_available_software(self):
        available_virtual_packages = []

        # Since this program is not meant to update Java,
        # Java version is not used.
        java_ver = ""
        java_core_vp = VirtualPackage("core-packages", "Java", java_ver)
        java_core_vp.is_installed = False
        java_core_vp.real_files = [
            {
                "name": "task-java-2019-1pclos2019.noarch.rpm",
                "base_url": configuration.PCLOS_repo_base_url
                + configuration.PCLOS_repo_path,
                "estimated_download_size": 1592,  # size in bytes
                "checksum": "",
            },
            {
                "name": "java-sun-16-2pclos2021.x86_64.rpm",
                "base_url": configuration.PCLOS_repo_base_url
                + configuration.PCLOS_repo_path,
                "estimated_download_size": 119920500,  # size in bytes
                "checksum": "",
            },
        ]
        recommended_Java_ver = ""
        available_virtual_packages.append(java_core_vp)

        # Decide which LO version should be recommended for installation
        if configuration.force_specific_LO_version != "":
            LO_ver = configuration.force_specific_LO_version
        else:
            LO_ver = configuration.latest_available_LO_version
        recommended_LO_ver = LO_ver
        LO_minor_ver = configuration.make_minor_ver(LO_ver)
        # Build VP for LO core package
        office_core_vp = VirtualPackage("core-packages", "LibreOffice", LO_ver)
        office_core_vp.is_installed = False
        office_core_vp.real_files = [
            {
                "name": "LibreOffice_" + LO_minor_ver + "_Linux_x86-64_rpm.tar.gz",
                "base_url": configuration.DocFund_base_url
                + LO_minor_ver
                + configuration.DocFund_path_ending,
                "estimated_download_size": 235265947,  # size in bytes
                "checksum": "md5",
            },
        ]
        available_virtual_packages.append(office_core_vp)

        # Build VPs for langpacks except en-US language pack,
        # it is only installed/removed together with
        # core package and should not be offered for install separately
        for lang_code in configuration.supported_langs.keys() - {"en-US"}:
            office_lang_vp = VirtualPackage(lang_code, "LibreOffice", LO_ver)
            office_lang_vp.is_installed = False
            office_lang_vp.real_files = [
                {
                    "name": "LibreOffice_"
                    + LO_minor_ver
                    + "_Linux_x86-64_rpm_langpack_"
                    + lang_code
                    + ".tar.gz",
                    "base_url": configuration.DocFund_base_url
                    + LO_minor_ver
                    + configuration.DocFund_path_ending,
                    "estimated_download_size": 17366862,  # size in bytes
                    "checksum": "md5",
                }
            ]
            if lang_code in configuration.existing_helppacks:
                office_lang_vp.real_files.append(
                    {
                        "name": "LibreOffice_"
                        + LO_minor_ver
                        + "_Linux_x86-64_rpm_helppack_"
                        + lang_code
                        + ".tar.gz",
                        "base_url": configuration.DocFund_base_url
                        + LO_minor_ver
                        + configuration.DocFund_path_ending,
                        "estimated_download_size": 3654837,  # size in bytes
                        "checksum": "md5",
                    }
                )
            available_virtual_packages.append(office_lang_vp)

        # Build VP for Clipart core package
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
                "estimated_download_size": 8927046,  # size in bytes
                "checksum": "",
            },
            {
                "name": "clipart-openclipart-2.0-1pclos2021.x86_64.rpm",
                "base_url": configuration.PCLOS_repo_base_url
                + configuration.PCLOS_repo_path,
                "estimated_download_size": 899116547,  # size in bytes
                "checksum": "",
            },
        ]
        recommended_Clip_ver = configuration.latest_available_clipart_version
        available_virtual_packages.append(clipart_core_vp)

        nice_list = " | ".join(
            [
                str(p.family) + " " + str(p.version) + " " + str(p.kind)
                for p in available_virtual_packages
            ]
        )
        log.debug(f"available software: " + nice_list)
        return (
            available_virtual_packages,
            recommended_Java_ver,
            recommended_LO_ver,
            recommended_Clip_ver,
        )

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

        nice_list = " || ".join([str(p) for p in installed_virtual_packages])
        log.info(_("found_software: {}").format(nice_list))
        return installed_virtual_packages

    def _make_changes(
        self,
        virtual_packages,
        rpms_and_tgzs_to_use,
        create_offline_copy,
        progress_reporter,
    ):
        # At this point normal changes procedure and local copy install
        # procedure converge and thus use the same function

        # STEP
        progress_reporter.step_start(_("Trying to stop LibreOffice quickstarter"))
        self._terminate_LO_quickstarter()
        progress_reporter.step_end()

        # STEP
        # Java needs to be installed?
        # (Note that Java may have been downloaded as a result of
        #  force_java_download but not actually marked for install)
        java_package = [
            c for c in self.package_tree_root.children if "Java" in c.family
        ][0]
        if (
            java_package.is_marked_for_install
            and rpms_and_tgzs_to_use["files_to_install"]["Java"]
        ):
            progress_reporter.step_start(_("Installing Java"))

            is_installed, expl = self._install_Java(
                rpms_and_tgzs_to_use["files_to_install"]["Java"],
                progress_reporter,
            )
            if is_installed is False:
                msg = _("Java installation failed: ")
                self.inform_user(msg, expl, isOK=False)
                return
            progress_reporter.step_end()
        else:
            progress_reporter.step_skip(_("Java needs not to be installed"))

        # At this point everything that is needed is downloaded and verified,
        # also Java is installed (except in unlikely case in which the user
        # only installs Clipart).
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
            progress_reporter.step_start(_("Removing selected Office components"))

            is_removed, expl = self._uninstall_office_components(
                office_packages_to_remove,
                progress_reporter,
            )

            if is_removed is False:
                msg = _("Failed to remove Office components: ")
                self.inform_user(msg, expl, isOK=False)
                return
            progress_reporter.step_end()
        else:
            progress_reporter.step_skip(_("No Office components need to be removed"))

        # STEP
        # Any Office components need to be installed?
        if (
            rpms_and_tgzs_to_use["files_to_install"]["LibreOffice-core"]
            or rpms_and_tgzs_to_use["files_to_install"]["LibreOffice-langs"]
        ):
            progress_reporter.step_start(_("Installing selected Office components"))

            is_installed, expl = self._install_office_components(
                rpms_and_tgzs_to_use["files_to_install"]["LibreOffice-core"],
                rpms_and_tgzs_to_use["files_to_install"]["LibreOffice-langs"],
                progress_reporter,
            )
            if is_installed is False:
                msg = _("Failed to install Office components: ")
                self.inform_user(msg, expl, isOK=False)
                return

            progress_reporter.step_end()
        else:
            progress_reporter.step_skip(_("No Office components need to be installed"))

        # STEP
        # Clipart library is to be removed?
        clipart_packages_to_remove = [
            p
            for p in virtual_packages
            if p.family == "Clipart" and p.is_marked_for_removal
        ]
        if clipart_packages_to_remove:
            progress_reporter.step_start(_("Removing Clipart library"))

            is_removed, expl = self._uninstall_clipart(
                clipart_packages_to_remove,
                progress_reporter,
            )

            if is_removed is False:
                msg = _("Failed to remove Clipart library: ")
                self.inform_user(msg, expl, isOK=False)
                return
            progress_reporter.step_end()
        else:
            progress_reporter.step_skip(_("Clipart needs not to be removed"))

        # STEP
        # Clipart library is to be installed?
        if rpms_and_tgzs_to_use["files_to_install"]["Clipart"]:
            progress_reporter.step_start("Installing Clipart library")

            is_installed, expl = self._install_clipart(
                rpms_and_tgzs_to_use["files_to_install"]["Clipart"],
                progress_reporter,
            )
            if is_installed is False:
                msg = _("Openclipart installation failed: ")
                self.inform_user(msg, expl, isOK=False)
                return
            progress_reporter.step_end()
        else:
            progress_reporter.step_skip(_("Clipart needs not to be installed"))

        # STEP
        # Should downloaded packages be kept ?
        if create_offline_copy is True:
            progress_reporter.step_start(_("Saving packages"))

            is_saved, expl = PCLOS.move_dir(
                configuration.verified_dir, configuration.offline_copy_dir
            )
            if is_saved is False:
                msg = _("Failed to save packages: ")
                self.inform_user(msg, expl, isOK=False)
                return
            else:
                msg = _(
                    "All changes successful\nPackages saved to {}.\n"
                    "This directory is getting wiped out on reboot, "
                    "please move it to some other location."
                ).format(configuration.offline_copy_dir)
                self.inform_user(msg, expl, isOK=True)
            progress_reporter.step_end()
        else:
            msg = _("All changes successful")
            self.inform_user(msg, "", isOK=True)
            progress_reporter.step_skip(_("Packages were not saved for later use"))

    def _collect_packages(
        self,
        packages_to_download: list,
        progress_reporter,
        skip_verify=False,
    ) -> tuple[bool, str, dict]:
        """Checks files availability on remote server(s) and downloads them

        Files to download (with URLs) are obtained from the
        VirtualPackage objects passed.
        This function first verifies that all requested files exists
        on the server(s) before starting the download process.
        (Returns False if any uri is not valid)
        Each file and its MD5 checksum (if one exist) is downloaded
        and file is verified against it. Function will return error at any point
        during this process (eg. file can't be downloaded or verification fails)
        and will not continue with download.

        Parameters
        ----------
        progress_reporter : Callable
        Callback used to report download progress

        skip_verify : bool
        Skip the md5 verification if set True (default False)

        packages_to_download : list
        Virtual packages list to download

        Returns
        -------
        tuple[bool, str, dict]
        T/F success/failure, str with explanation for error (empty is success)
        dict with absolute path do downloaded files
        """

        rpms_and_tgzs_to_use = {
            "files_to_install": {
                "Java": [],
                "LibreOffice-core": [],
                "LibreOffice-langs": [],
                "Clipart": [],
            },
        }

        nice_list = " | ".join(
            [
                str(p.family) + " " + str(p.version) + " " + str(p.kind)
                for p in packages_to_download
            ]
        )
        log.debug(_("Packages to download: ") + nice_list)

        # Check if there is connection to the server(s)
        # and requested files exist.
        for package in packages_to_download:
            for file in package.real_files:
                url = file["base_url"] + file["name"]
                is_available, msg = net.check_url_available(url)
                if not is_available:
                    return (False, msg, rpms_and_tgzs_to_use)

        for package in packages_to_download:
            for file in package.real_files:
                f_url = file["base_url"] + file["name"]
                f_dest = configuration.working_dir.joinpath(file["name"])

                is_downloaded, error_msg = net.download_file(
                    f_url,
                    f_dest,
                    progress_reporter,
                )
                if not is_downloaded:
                    msg = _("Error while trying to download {}: ").format(f_url)
                    msg = msg + error_msg
                    return (False, msg, rpms_and_tgzs_to_use)

                if file["checksum"] and not skip_verify:
                    checksum_file = file["name"] + "." + file["checksum"]
                    csf_url = file["base_url"] + checksum_file
                    csf_dest = configuration.working_dir.joinpath(checksum_file)

                    is_downloaded, error_msg = net.download_file(
                        csf_url,
                        csf_dest,
                        progress_reporter,
                    )
                    if not is_downloaded:
                        msg = _("Error while trying to download {}: ").format(csf_url)
                        msg = msg + error_msg
                        return (False, msg, rpms_and_tgzs_to_use)

                    is_correct = net.verify_checksum(
                        f_dest, csf_dest, progress_reporter
                    )
                    if not is_correct:
                        msg = _("Verification of the {} failed").format(file["name"])
                        return (False, msg, rpms_and_tgzs_to_use)

                    if not PCLOS.remove_file(csf_dest):
                        msg = _("Error removing file {}").format(csf_dest)
                        return (False, msg, rpms_and_tgzs_to_use)

                # Move file to verified files directory
                if package.family == "LibreOffice":
                    if package.is_langpack():
                        ending = "-langs"
                    else:
                        ending = "-core"
                    label = package.family + ending
                    dir_name = label + "_tgzs"
                else:
                    label = package.family
                    dir_name = label + "_rpms"
                f_verified = configuration.verified_dir.joinpath(dir_name)
                f_verified = f_verified.joinpath(file["name"])
                if not PCLOS.move_file(from_path=f_dest, to_path=f_verified):
                    msg = _("Error moving file {} to {}").format(f_dest, f_verified)
                    return (False, msg, rpms_and_tgzs_to_use)
                # Add absolute file path to verified files list
                rpms_and_tgzs_to_use["files_to_install"][label].append(f_verified)

        log.debug(_("rpms_and_tgzs_to_use: {}").format(rpms_and_tgzs_to_use))
        return (True, "", rpms_and_tgzs_to_use)

    def _terminate_LO_quickstarter(self):
        LO_PIDs = PCLOS.get_PIDs_by_name(["libreoffice"]).get("libreoffice")
        OO_PIDs = PCLOS.get_PIDs_by_name(["OpenOffice"]).get("OpenOffice")
        if LO_PIDs:
            for pid in LO_PIDs:
                if int(pid) > 1500:  # pseudo safety
                    log.info(
                        _("Terminating LibreOffice quickstarter (PID: {})").format(pid)
                    )
                    PCLOS.run_shell_command("kill -9 {pid}")
                else:
                    log.warning(
                        _(
                            "quickstarter PID ({}) is suspiciously low "
                            "- refusing to kill process"
                        ).format(pid)
                    )
        if OO_PIDs:
            for pid in OO_PIDs:
                if int(pid) > 1500:
                    log.info(
                        _("Terminating OpenOffice quickstarter (PID: {})").format(pid)
                    )
                    PCLOS.run_shell_command("kill -9 {pid}")
                else:
                    log.warning(
                        _(
                            "quickstarter PID ({}) is suspiciously low "
                            "- refusing to kill process"
                        ).format(pid)
                    )
        if (not LO_PIDs) and (not OO_PIDs):
            log.info(_("No running quickstarter found ...good"))

    def _install_Java(
        self,
        java_rpms: dict,
        progress_reporter: Callable,
    ) -> tuple[bool, str]:
        # 1) Move files (task-java and java-sun) from
        #    verified copy directory to /var/cache/apt/archives
        cache_dir = pathlib.Path("/var/cache/apt/archives/")
        package_names = []
        for file in java_rpms:
            if not PCLOS.move_file(
                from_path=file, to_path=cache_dir.joinpath(file.name)
            ):
                return (False, _("Java not installed, error moving file"))
            # rpm name != rpm filename
            rpm_name = "-".join(file.name.split("-")[:2])
            package_names.append(rpm_name)

        # 2) Use apt-get to install those 2 files
        is_installed, msg = PCLOS.install_using_apt_get(
            package_nameS=package_names,
            progress_reporter=progress_reporter,
        )
        if is_installed is False:
            return (False, msg)

        # 3) move rpm files back to storage
        for file in java_rpms:
            if not PCLOS.move_file(
                from_path=cache_dir.joinpath(file.name), to_path=file
            ):
                return (False, _("Java installed but there was error moving file"))

        return (True, _("Java successfully installed"))

    def _uninstall_office_components(
        self,
        packages_to_remove: list,
        progress_reporter: Callable,
    ) -> tuple[bool, str]:
        # rpms_to_rm is always a minimal subset of rpms that once
        # marked for removal will cause all dependencies to be removed too.

        nice_list = " | ".join(
            [
                str(p.family) + " " + str(p.version) + " " + str(p.kind)
                for p in packages_to_remove
            ]
        )
        log.debug(_("Packages to remove: ") + nice_list)

        users = PCLOS.get_system_users()

        # First get rid of any OpenOffice installation
        OpenOfficeS = [p for p in packages_to_remove if p.family == "OpenOffice"]
        dirs_to_rm = []
        files_to_remove = []
        rpms_to_rm = []
        for oo in OpenOfficeS:
            # OpenOffice removal procedures
            if oo.version.startswith("2."):  # any series 2.x
                rpms_to_rm.extend(["openoffice.org", "openoffice.org-mimelnk"])
                # Leftover files and directories to remove
                for user in users:
                    dirs_to_rm.append(user.home_dir.joinpath(".ooo-2.0"))
                    dirs_to_rm.append(user.home_dir.joinpath(f".ooo-{oo.version}"))
            if oo.version == "3.0.0":  # ver. 3.0.0 only
                rpms_to_rm.extend(["openoffice.org-core"])
                # Leftover files and directories to remove
                for user in users:
                    dirs_to_rm.append(user.home_dir.joinpath(".ooo3"))
                    dirs_to_rm.append(user.home_dir.joinpath(".config/ooo3"))
                for leftover_dir in pathlib.Path("/opt").glob("openoffice*"):
                    dirs_to_rm.append(leftover_dir)
            if oo.version.startswith("3.") and oo.version != "3.0.0":  # any later
                rpms_to_rm.append("openoffice.org-ure")
                rpms_to_rm.append(f"openoffice.org{oo.version}-mandriva-menus")
                # Leftover files and directories to remove
                for user in users:
                    dirs_to_rm.append(user.home_dir.joinpath(".ooo3"))
                    dirs_to_rm.append(user.home_dir.joinpath(".config/ooo3"))
                    files_to_remove.append(
                        user.home_dir.joinpath("OpenOffice_Info.txt")
                    )
                    files_to_remove.append(
                        user.home_dir.joinpath("getopenoffice.desktop")
                    )
                s_files = [
                    pathlib.Path("/etc/skel/").joinpath("OpenOffice_Info.txt"),
                    pathlib.Path("/etc/skel_fm/").joinpath("OpenOffice_Info.txt"),
                    pathlib.Path("/etc/skel_default/").joinpath("OpenOffice_Info.txt"),
                    pathlib.Path("/etc/skel-orig/").joinpath("OpenOffice_Info.txt"),
                ]
                files_to_remove.extend(s_files)
                dirs_to_rm.extend(pathlib.Path("/opt").glob("openoffice*"))
        if OpenOfficeS:
            # Remove
            log.debug(_("OO rpms_to_rm: {}").format(rpms_to_rm))
            s, msg = PCLOS.uninstall_using_apt_get(rpms_to_rm, progress_reporter)
            if not s:
                return (False, msg)
            # Do post-removal cleanup
            log.debug(_("Dirs to remove: {}").format(dirs_to_rm))
            map(PCLOS.force_rm_directory, dirs_to_rm)
            log.debug(_("Files to remove: {}").format(files_to_remove))
            map(PCLOS.remove_file, files_to_remove)
            # update menus
            PCLOS.update_menus()

        # Now let's deal with LibreOffice's language packs.
        # User may want to remove just that (no core package uninstall)
        # in which case we are going to be done.
        # Alternatively core package is also marked for removal and will be
        # uninstalled in the later step.
        # Such ordering will not interfere with dependencies,
        # as language packs are optional additions anyway.

        # Never remove en-US language pack on its own
        # (it is only installed/removed together with core package)
        LibreOfficeLANGS = [
            p
            for p in packages_to_remove
            if ((p.family == "LibreOffice") and p.is_langpack() and (p.kind != "en-US"))
        ]
        dirs_to_rm = []
        files_to_remove = []
        rpms_to_rm = []
        for lang in LibreOfficeLANGS:
            # LibreOffice langs removal procedures.
            base_version = configuration.make_base_ver(lang.version)

            expected_rpm_names = [
                f"libreoffice{base_version}-{lang.kind}-",
                f"libobasis{base_version}-{lang.kind}-",
                f"libobasis{base_version}-{lang.kind}-help-",
            ]
            # a) Never remove English, Spanish and French dictionaries when
            # removing langpacks. These 3 dictionaries are provided by the
            # core package and should be kept installed for as long as
            # it is installed.
            excluded = ["en", "es", "fr"]
            # b) Only remove dictionary package if no other regional package
            # sharing this dictionary will remain.
            base_lang_code = lang.kind.split("-")[0]
            langs_with_the_same_base_code_marked_4_removal = [
                p.is_marked_for_removal
                for p in (lang.get_siblings() + [lang])
                if (p.kind.startswith(base_lang_code) and p.is_installed)
            ]

            if not any([lang.kind.startswith(exl) for exl in excluded]) and all(
                langs_with_the_same_base_code_marked_4_removal
            ):
                expected_rpm_names.append(
                    f"libreoffice{base_version}-dict-{base_lang_code}-"
                )

            for candidate in expected_rpm_names:
                success, reply = PCLOS.run_shell_command(f"rpm -qa | grep {candidate}")
                if not success:
                    return (False, _("Failed to run shell command"))
                else:
                    if reply:
                        rpms_to_rm.append(candidate[:-1])
        if LibreOfficeLANGS:
            log.debug(_("LO langs rpms_to_rm: {}").format(rpms_to_rm))
            s, msg = PCLOS.uninstall_using_apt_get(rpms_to_rm, progress_reporter)
            if not s:
                return (False, msg)

        # Finally remove LibreOffice core if marked for removal
        LibreOfficeCORE = [
            p
            for p in packages_to_remove
            if (p.family == "LibreOffice" and p.is_corepack())
        ]
        dirs_to_rm = []
        files_to_remove = []
        rpms_to_rm = []
        for core in LibreOfficeCORE:
            # Removal procedures for LibreOffice core.
            if core.version.startswith("3.3"):  # 3.3 and its subvariants
                rpms_to_rm.append(f"libreoffice3-ure")
                rpms_to_rm.append(f"libreoffice{core.version}-mandriva-menus")
                # Leftover files and directories to remove
                for user in users:
                    dirs_to_rm.append(user.home_dir.joinpath(".libreoffice"))
                    dirs_to_rm.append(user.home_dir.joinpath(".config/libreoffice"))
                    files_to_remove.append(
                        user.home_dir.joinpath("Desktop/lomanager.desktop")
                    )
                    kdedir = user.home_dir.joinpath(".kde4/vdt/2/2a")
                    if kdedir.exists():
                        files_to_remove.extend(kdedir.glob("LO*"))
                skel_fm_dir = pathlib.Path("/etc/skel_fm").joinpath(".kde4/vdt/2/2a")
                if skel_fm_dir.exists():
                    files_to_remove.extend(skel_fm_dir.glob("LO*"))
                for leftover_dir in pathlib.Path("/opt").glob("libreoffice*"):
                    dirs_to_rm.append(leftover_dir)
                for icon in pathlib.Path("/usr/share/icons").glob("libreoffice-*"):
                    files_to_remove.append(icon)

            # All other versions (with subvariants) starting from 3.4 and later
            # (Historically these were:
            #  3.4, 3.5, 3.6, 4.0, 4.1, 4.2, 4.3, 4.4, 5.0, 5.1, 5.2, 5.3,
            #  5.4, 6.0, 6.1, 6.2, 6.3, 6.4, 7.0,7.1, 7.2, 7.3, 7.4, 7.5)
            else:
                base_version = configuration.make_base_ver(core.version)
                # All if-s in case (extremely unlikely) someone managed to
                # install more then one version
                if core.version.startswith("3.4"):
                    rpms_to_rm.append(f"libreoffice{base_version}-ure")
                    rpms_to_rm.append(f"libreoffice{base_version}-mandriva-menus")
                if (
                    core.version.startswith("3.5")
                    or core.version.startswith("3.6")
                    or core.version.startswith("4.0")
                ):
                    rpms_to_rm.append(f"libreoffice{base_version}-ure")
                    rpms_to_rm.append(f"libreoffice{base_version}-stdlibs")
                    rpms_to_rm.append(f"libreoffice{base_version}-mandriva-menus")
                if (
                    core.version.startswith("3.4") is False
                    and core.version.startswith("3.5") is False
                    and core.version.startswith("3.6") is False
                    and core.version.startswith("4.0") is False
                ):
                    rpms_to_rm.append(f"libreoffice{base_version}-ure")
                    rpms_to_rm.append(f"libreoffice{base_version}-freedesktop-menus")
                    rpms_to_rm.append(f"libobasis{base_version}-ooofonts")
                # Leftover files and directories to remove (common for all vers.)
                for user in users:
                    dirs_to_rm.append(user.home_dir.joinpath(".libreoffice"))
                    dirs_to_rm.append(user.home_dir.joinpath(".config/libreoffice"))
                    files_to_remove.append(
                        user.home_dir.joinpath("Desktop/lomanager.desktop")
                    )
                for dir in pathlib.Path("/etc/skel/.config").glob("libreoffice*"):
                    dirs_to_rm.append(dir)
                for leftover_dir in pathlib.Path("/opt").glob("libreoffice*"):
                    dirs_to_rm.append(leftover_dir)
                for icon in pathlib.Path("/usr/share/icons").glob("libreoffice*"):
                    files_to_remove.append(icon)
        if LibreOfficeCORE:
            # Remove
            log.debug(_("LO core rpms_to_rm: {}").format(rpms_to_rm))
            s, msg = PCLOS.uninstall_using_apt_get(rpms_to_rm, progress_reporter)
            if not s:
                return (False, msg)
            # Do post-removal cleanup
            log.debug(_("Dirs to remove: {}").format(dirs_to_rm))
            map(PCLOS.force_rm_directory, dirs_to_rm)
            log.debug(_("Files to remove: {}").format(files_to_remove))
            map(PCLOS.remove_file, files_to_remove)
            # update menus
            PCLOS.update_menus()

        uninstall_msg = _("Packages successfully uninstalled")
        return (True, uninstall_msg)

    def _install_office_components(
        self,
        LO_core_tgzS: dict,
        LO_langs_tgzS: dict,
        progress_reporter: Callable,
    ) -> tuple[bool, str]:
        PCLOS.clean_dir(configuration.working_dir)

        rpms_c = []
        rpms_l = []
        if LO_core_tgzS:
            tgz = LO_core_tgzS[0]
            log.debug(_("Core tar.gz found"))
            rpms_c = PCLOS.extract_tgz(tgz)
        if LO_langs_tgzS:
            for tgz in LO_langs_tgzS:
                log.debug(_("Lang/Help pack tar.gz found"))
                rpms_l += PCLOS.extract_tgz(tgz)

        rpms = rpms_c + rpms_l
        if rpms:
            # Some rpm should be installed

            rpms_to_install = [r for r in rpms if "-kde-integration-" not in str(r)]
            kde_rpms = [r for r in rpms if "-kde-integration-" in str(r)]
            for rpm in kde_rpms:
                PCLOS.remove_file(rpm)

            log.debug(_("Extracted rpm files to install"))
            for rpm in rpms_to_install:
                log.debug(rpm)

            is_installed, msg = PCLOS.install_using_rpm(
                rpms_to_install,
                progress_reporter,
            )

            PCLOS.clean_dir(configuration.working_dir)

            if is_installed is False:
                return (False, msg)

            # Post install stuff
            progress_reporter.progress_msg(
                _("Disabling LibreOffice's online updates...")
            )
            progress_reporter.progress(50)
            self._disable_LO_update_checks()
            progress_reporter.progress(100)

            progress_reporter.progress_msg(_("Modifying .desktop files..."))
            progress_reporter.progress(50)
            self._modify_dot_desktop_files()
            progress_reporter.progress(100)

            progress_reporter.progress_msg(_("Applying icon fixes..."))
            progress_reporter.progress(50)
            self._fix_LXDE_icons()
            progress_reporter.progress(100)

            # Finally return success
            return (True, _("LibreOffice packages successfully installed"))

        else:
            msg = _("No rpms extracted")
            log.error(msg)
            return (False, msg)

    def _disable_LO_update_checks(self):
        log.info(_("Preventing LibreOffice from checking for updates on its own"))

        # -- helper functions --
        def register_all_namespaces(f_name):
            namespaces = dict(
                [node for _, node in ET.iterparse(f_name, events=["start-ns"])]
            )
            for ns in namespaces:
                ET.register_namespace(ns, namespaces[ns])

        def add_disabled_autocheck(root):
            uc_item = ET.SubElement(root, "item")
            uc_item.set(
                "oor:path",
                r"/org.openoffice.Office.Jobs/Jobs/org.openoffice.Office.Jobs:Job['UpdateCheck']/Arguments",
            )
            uc_prop = ET.SubElement(uc_item, "prop")
            uc_prop.set("oor:name", "AutoCheckEnabled")
            uc_prop.set("oor:op", "fuse")
            uc_prop.set("oor:type", "xs:boolean")
            uc_val = ET.SubElement(uc_prop, "value")
            uc_val.text = "false"

        def create_xcu_file_w_disabled_autocheck(file: pathlib.Path):
            ET.register_namespace("oor", "https://openoffice.org/2001/registry")
            xml_root = ET.Element("{https://openoffice.org/2001/registry}items")
            add_disabled_autocheck(root=xml_root)
            xml_tree = ET.ElementTree(xml_root)
            xml_tree.write(
                file,
                xml_declaration=True,
                method="xml",
                encoding="UTF-8",
            )

        def find_autocheck_prop(root):
            value = ET.Element("value")
            for property in root.iter("prop"):
                if "AutoCheckEnabled" in property.attrib.values():
                    return property.find("value")
            return value

        # -- end helper functions --

        # Disable checks for every existing user
        for user in PCLOS.get_system_users():
            log.debug(f"changing registrymodifications.xcu for user: {user.name}")
            conf_dir_root = user.home_dir.joinpath(".config/libreoffice")
            conf_dir = conf_dir_root.joinpath("4/user")
            xcu_file = conf_dir.joinpath("registrymodifications.xcu")
            if xcu_file.exists():
                # modify existing file
                register_all_namespaces(xcu_file)
                xml_tree = ET.parse(xcu_file)
                xml_root = xml_tree.getroot()
                value = find_autocheck_prop(root=xml_root)
                if value is None or value.text is None:
                    # property does not exist, add it
                    add_disabled_autocheck(root=xml_root)
                else:
                    # property exists.
                    # set its value to false (even if it's false already)
                    value.text = "false"

                xml_tree.write(
                    xcu_file,
                    xml_declaration=True,
                    method="xml",
                    encoding="UTF-8",
                )
            else:
                # LibreOffice was never started by this user
                # Create new xcu_file with auto checks disabled
                if not conf_dir.exists():
                    PCLOS.make_dir_tree(target_dir=conf_dir)
                create_xcu_file_w_disabled_autocheck(file=xcu_file)
            # Set/reset files and folders ownership
            log.debug(f"reseting ownership of: {conf_dir_root}")
            os.chown(conf_dir_root, user.uid, user.gid)
            for item in conf_dir.iterdir():
                log.debug(f"reseting ownership of: {item}")
                os.chown(item, user.uid, user.gid)

        # Disable checking for new users (if ever created)
        skel_dir = pathlib.Path("/etc/skel/.config/libreoffice/4/user")
        skel_xcu_file = skel_dir.joinpath("registrymodifications.xcu")
        if not skel_xcu_file.exists():
            log.debug(f"no xcu in skel creating new one")
            if not skel_dir.exists():
                PCLOS.make_dir_tree(target_dir=skel_dir)
            create_xcu_file_w_disabled_autocheck(file=skel_xcu_file)

    def _modify_dot_desktop_files(self):
        # .desktop files shipped with LibreOffice contain the line:
        # Categories=Office;Spreadsheet;X-Red-Hat-Base;
        # Change it to:
        # Categories=Office;
        log.info(_("updating .desktop files"))
        base_dirS = [d for d in pathlib.Path("/opt").glob("libreoffice*") if d.is_dir()]
        fileS = [
            "base.desktop",
            "calc.desktop",
            "draw.desktop",
            "impress.desktop",
            "math.desktop",
            "writer.desktop",
        ]
        for dir in base_dirS:
            for file in fileS:
                fp = dir.joinpath("share/xdg").joinpath(file)
                if fp.exists():
                    with open(fp, "r") as infile:
                        config_lineS = infile.readlines()

                    with open(fp, "w") as outfile:
                        for line in config_lineS:
                            if line.startswith("Categories="):
                                outfile.write("Categories=Office;\n")
                            else:
                                outfile.write(line)
        # Refresh menus
        PCLOS.update_menus()

    def _fix_LXDE_icons(self):
        log.info(_("Applying fix for LXDE icons"))
        iconS = pathlib.Path("/usr/share/icons/hicolor/32x32/apps").glob(
            "libreoffice7*"
        )
        for icon in iconS:
            PCLOS.run_shell_command(f"ln -fs {icon} /usr/share/icons/")
        if pathlib.Path("/usr/bin/lxpanelctl").exists():
            PCLOS.run_shell_command(f"/usr/bin/lxpanelctl restart")
        PCLOS.update_menus()

    def _uninstall_clipart(
        self,
        c_art_pkgs_to_rm: list,
        progress_reporter: Callable,
    ) -> tuple[bool, str]:
        # For now it doesn't seem that openclipart rpm package name
        # includes version number so getting this information
        # from c_art_pkgs_to_rm is not necessary.
        rpms_to_rm = []
        expected_rpm_names = ["libreoffice-openclipart", "clipart-openclipart"]
        for candidate in expected_rpm_names:
            success, reply = PCLOS.run_shell_command(f"rpm -qa | grep {candidate}")
            if not success:
                return (False, _("Failed to run shell command"))
            else:
                if reply:
                    rpms_to_rm.append(candidate)
        s, msg = PCLOS.uninstall_using_apt_get(rpms_to_rm, progress_reporter)
        if not s:
            return (False, msg)
        return (True, _("Openclipart successfully removed"))

    def _install_clipart(
        self,
        clipart_rpmS,
        progress_reporter: Callable,
    ) -> tuple[bool, str]:
        # Use rpm to install clipart rpm packages
        # (sitting in verified_dir)
        is_installed, msg = PCLOS.install_using_rpm(
            clipart_rpmS,
            progress_reporter,
        )
        if is_installed is False:
            return (False, msg)
        return (True, _("Openclipart successfully installed"))

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
            # Search for: task-java-<something>.rpm, java-sun-<something>.rpm
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
                log.info(_("Found Java rpm packages: ") + msg)
            else:
                log.warning(_("No usable Java rpm packages found"))
        else:
            log.error(_("Java_rpms directory not found"))

        # 2) LibreOffice core packages directory
        LO_core_dir = pathlib.Path(local_copy_directory)
        LO_core_dir = LO_core_dir.joinpath("LibreOffice-core_tgzs")
        log.info(_("Checking {}").format(LO_core_dir))
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
                log.info(_("Found LibreOffice archive: ") + LO_core_tgzs[0])
            else:
                log.warning(_("No usable LibreOffice archive found"))
        else:
            log.error(_("LibreOffice-core_tgzs directory not found"))

        # 3) LibreOffice lang and help packages directory
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
            #  is not checked)
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
                            log.info(_("LibreOffice lang and helppacks found: ") + msg)
                        else:
                            log.warning(
                                _(
                                    "LibreOffice langpack(s) found in the "
                                    "local copy directory but their "
                                    "version(s) do not match LibreOffice "
                                    "core package version. Langpack(s) "
                                    "will not be installed. Found: "
                                )
                                + msg
                            )
                    else:
                        log.warning(
                            _(
                                "LibreOffice lang and helppacks found but "
                                "LibreOffice core was not found. Installation "
                                "of just the lang/helppacks is not supported. "
                                "Lang and helppacks found: "
                            )
                            + msg
                        )
                else:
                    log.warning(
                        _(
                            "Found lang and helppacks have inconsistent "
                            "versions and will not be used."
                        )
                    )
            else:
                log.warning(_("No usable lang or helppacks found"))
        else:
            log.error(_("LibreOffice-langs_tgzs directory not found"))

        # 4) Clipart directory
        Clipart_dir = pathlib.Path(local_copy_directory)
        Clipart_dir = Clipart_dir.joinpath("Clipart_rpms")
        log.info(_("Checking {}").format(Clipart_dir))
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
                log.info(_("Found Openclipart rpm packages: ") + msg)
            else:
                log.warning(_("No usable Openclipart rpm packages found"))
        else:
            log.error(_("Clipart_rpms directory not found"))

        log.debug(_("Java is present: {}").format(Java_local_copy["isPresent"]))
        log.debug(
            _("LO core is present: {}").format(LibreOffice_core_local_copy["isPresent"])
        )
        log.debug(
            _("LO langs is present: {}").format(
                LibreOffice_langs_local_copy["isPresent"]
            )
        )
        log.debug(
            _("Clipart lib is present: {}").format(Clipart_local_copy["isPresent"])
        )
        return (
            Java_local_copy,
            LibreOffice_core_local_copy,
            LibreOffice_langs_local_copy,
            Clipart_local_copy,
        )

    def _space_for_download(
        self, packages_to_download: list[VirtualPackage]
    ) -> tuple[bool, str, str]:
        needed = 0
        for p in packages_to_download:
            for file in p.real_files:
                needed += file["estimated_download_size"]
        available = PCLOS.free_space_in_dir(configuration.working_dir)
        is_enough = available > needed

        def get_size_string(bytes_size):
            if bytes_size / (1024**3) < 1:
                if bytes_size / (1024**2) < 1:
                    if bytes_size / 1024 < 1:
                        return str(bytes_size) + " bytes"
                    else:
                        return str(round(bytes_size / (1024**1))) + " KiB"
                else:
                    return str(round(bytes_size / (1024**2))) + " MiB"
            else:
                return str(round(bytes_size / (1024**3))) + " GiB"

        needed_str = get_size_string(needed)
        available_str = get_size_string(available)
        log.debug(_("Total size of packages to download: {}").format(needed_str))
        log.debug(
            _(
                "Free space available in {}: {}".format(
                    configuration.working_dir, available_str
                )
            )
        )

        return (is_enough, needed_str, available_str)

    # -- end Private methods of MainLogic
