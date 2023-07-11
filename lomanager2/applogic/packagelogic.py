import time  # TODO: just for the tests
import re
import pathlib
import configuration
from configuration import logging as log
from typing import Any, Tuple
from . import PCLOS
from .datatypes import VirtualPackage, SignalFlags


class MainLogic(object):
    # Only 1 objects of this class will exists.
    # So this could have been done by placing
    # the variables, statements and functions directly in a module.
    # But this would then run these at module import
    # and I don't want to put import statements
    # in the middle of a code or brake code's intelligibility
    # by importing some logic at the top of the main file.
    def __init__(self) -> None:
        # TODO: Implement
        # 1) Create working folder at PATH obtained from configuration.
        #    Something along the lines:
        #    PCLOS.create_folder(configuration.temp_folder_path)

        # 2) Create state objects
        self._warnings = [{"explanation": "", "data": ""}]
        self.global_flags = SignalFlags()
        self._latest_available_LO_version = ""
        self._latest_available_clipart_version = ""
        self._virtual_packages = []
        self._latest_available_packages = []
        # self._package_menu is created by the refresh_state method

        # 3) Run flags_logic
        any_limitations, self._warnings = self._flags_logic()
        if any_limitations is True:
            # TODO: Somehow the adapter or view have to be informed that
            #       some there are warnings that the user needs to see.
            #       How to to this avoiding Qt signal/slot mechanism
            #       which will make this code not reusable in CLI ?
            pass

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
        space_available = PCLOS.get_disk_space()
        # 4) set "ready for state transition flag" (T/F) accordingly
        # 5) add warning message to self._warnings if not enough space
        if total_space_needed < space_available:
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
        return self._warnings

    def apply_changes(self, *args, **kwargs):
        log.warning("WIP !!!")
        log.debug(
            f"Flag <<ready_to_apply_changes>> is: "
            f"<<{self.global_flags.ready_to_apply_changes}>>"
        )
        # TODO: bypassing for tests
        log.warning(f"TEST: Manually SETTING <<ready_to_apply_changes>> <<True>>")
        self.global_flags.ready_to_apply_changes = True

        # Callback function for raporting the status of the procedure
        if "report_status" in kwargs.keys():
            status_callback = kwargs["report_status"]
        else:
            status_callback = None

        # Check if we can proceed with applying changes
        if self.global_flags.ready_to_apply_changes is False:
            explanation = "Not ready to apply requested changes."
            log.error(explanation)
            status = {"is_OK": False, "explanation": explanation}
            if status_callback is not None:
                status_callback(status)
            return status

        else:  # We are good to go
            # Set some variables here explicitly
            # Callback function for raporting overall procedure progress
            if "inform_about_progress" in kwargs.keys():
                progress_callback = kwargs["inform_about_progress"]
            else:
                progress_callback = None
            # Should downloaded packages be kept
            if "keep_packages" in kwargs.keys():
                keep_packages = kwargs["keep_packages"]
            else:
                status = {
                    "is_OK": False,
                    "explanation": "keep_packages argument is obligatory",
                }
                if status_callback is not None:
                    status_callback(status)
                return status

            # TODO: Java virtual package should already be in the list
            #       of virtual and no decision making should be done
            #       here other then marking java to be downloaded
            #       if this was requested by the user in the UI.
            # Decide what to do with Java
            #
            #    Create Java VirtualPackage for the install subprocedure
            #    to know what to do (here all java_package flags are False)
            java_package = VirtualPackage("core-packages", "Java", "")

            is_java_installed = self._gather_system_info()["is Java installed"]

            is_LO_core_requested_for_install = False
            for package in self._virtual_packages:
                if (
                    package.family == "LibreOffice"
                    and package.kind == "core-packages"
                    and package.is_marked_for_install
                ):
                    is_LO_core_requested_for_install = True
                    break

            if is_java_installed is False and is_LO_core_requested_for_install is True:
                java_package.is_to_be_downloaded = True
                java_package.is_marked_for_install = True

            if self.global_flags.force_download_java is True:
                java_package.is_to_be_downloaded = True

            #    Add Java VirtualPackage to the list
            self._virtual_packages.append(java_package)

            # Block any other calls of this function...
            self.global_flags.ready_to_apply_changes = False
            # ...and proceed with procedure
            log.info("Applying changes...")
            status = self._install(
                # TODO: passing property to method within class doesn't make sense
                #       Do I want for any reason pass a deepcopy here?
                #       or perhaps it will be different when _virtual_packages
                #       changes to tree rather then simple list?
                self._virtual_packages,
                keep_packages=keep_packages,
                callback_function=progress_callback,
            )
            return status

    def install_from_local_copy(self, *args, **kwargs):
        log.debug("WIP !!!")

        log.debug(
            f"Flag <<ready_to_apply_changes>> is: "
            f"<<{self.global_flags.ready_to_apply_changes}>>"
        )
        # TODO: bypassing for tests
        log.debug(f"TEST: Manually SETTING <<ready_to_apply_changes>> <<True>>")
        self.global_flags.ready_to_apply_changes = True

        log.debug(
            f"Flag <<block_local_copy_install>> is: "
            f"<<{self.global_flags.block_local_copy_install}>>"
        )
        log.debug(f"TEST: Manually SETTING <<block_local_copy_install>> <<False>>")
        self.global_flags.block_local_copy_install = False

        # Callback function for raporting the status of the procedure
        if "report_status" in kwargs.keys():
            status_callback = kwargs["report_status"]
        else:
            status_callback = None

        # Check if we can proceed with applying changes
        if self.global_flags.ready_to_apply_changes is False:
            explanation = "Not ready to apply requested changes."
            log.error(explanation)
            status = {"is_OK": False, "explanation": explanation}
            if status_callback is not None:
                status_callback(status)
            return status

        # Check if local copy installation was not blocked
        if self.global_flags.block_local_copy_install is True:
            explanation = "Local copy installation is not allowed."
            log.error(explanation)
            status = {"is_OK": False, "explanation": explanation}
            if status_callback is not None:
                status_callback(status)
            return status

        else:  # We are good to go
            # Set some variables here explicitly
            # Callback function for raporting overall procedure progress
            if "inform_about_progress" in kwargs.keys():
                progress_callback = kwargs["inform_about_progress"]
            else:
                progress_callback = None
            # Set local copy directory
            if "local_copy_folder" in kwargs.keys():
                local_copy_directory = kwargs["local_copy_folder"]
            else:
                status = {
                    "is_OK": False,
                    "explanation": "local_copy_folder argument is obligatory",
                }
                if status_callback is not None:
                    status_callback(status)
                return status

            # Block any other calls of this function...
            self.global_flags.ready_to_apply_changes = False
            # ...and proceed with procedure
            log.info("Applying changes...")
            status = self._local_copy_install_procedure(
                self._virtual_packages,
                local_copy_directory=local_copy_directory,
                callback_function=progress_callback,
            )
            return status

    def refresh_state(self):
        # Reset packages list
        self._virtual_packages = []
        # 4) Gather system information
        system_info = self._gather_system_info()

        # 5) Initialize state objects
        self._latest_available_LO_version = configuration.latest_available_LO_version
        self._latest_available_clipart_version = (
            configuration.latest_available_clipart_version
        )
        self._build_virtual_packages_list(system_info["installed software"])
        # TODO: This should not be done this way,
        #       latest_available_packages should not exist at all.
        #       All packages, both installed and available for install,
        #       should be added to _virtual_packages list with appropriate
        #       flags. It is then viewmodel's job to show/hide them from
        #       the user or present their state based on these flags
        #       (visible/disabled etc.) latest_available_packages is indeed
        #       a data source separate from installed_packages and has to be
        #       treated by main logic as such but it was not pictured
        #       explicitly in the flowchart - it is MainLogic job to deal
        #       with this data source. So the method
        #       _build_latest_available_packages_list is needed but this
        #       method is called only once on object creation since lomanager2
        #       is not and will not be (by design) capable of updating this
        #       list on demand. If the user updates the system and thus
        #       updates lomanager2 he needs to restart the app anyway
        #       and the app is constructing available packages list from
        #       the single version number and not fetching a list from
        #       an repo server.
        # TODO: having said all above I am keeping the concept of
        #       _latest_available_packages for now because its removal
        #       would require modifications in the PackageMenu class
        #       which is not a priority at the moment.
        #       So after this list is built here it is then passed to
        #       to PackageMenu constructor as an additional argument
        self._build_latest_available_packages_list(
            self._latest_available_LO_version,
            self._latest_available_clipart_version,
        )
        # TODO: Given that _latest_available_packages should be obsoleted
        #       and new packages added to _virtual_packages which of the last
        #       2 arguments passed here are really needed?
        # creates self._package_menu object
        # TODO: Since on initialization PackageMenu calls its method
        #       _set_initial_state it has to be made aware of the
        #       self._flags object
        # TODO: Implement additional logic in PackageMenu that
        #       restricts allowed package operations based on self._flags
        #       This is because flags may override any logic
        #       based only on package dependencies.
        self._package_menu = PackageMenu(
            self._virtual_packages,
            self._latest_available_packages,
            self._latest_available_LO_version,
            self._latest_available_clipart_version,
        )

    # -- end Public interface for MainLogic

    # -- Private methods of MainLogic
    def _gather_system_info(self) -> dict:
        """Queries the OS for information relevant to LibreOffice installation.

        Returns
        -------
        information : dict
            Useful information
        """

        log.debug("WIP !" "Sending dummy data !!!")
        system_info = dict()

        # TODO: Implement
        # system_information["current locale"] = get_current_locale()
        system_info["live session"] = PCLOS.is_live_session_active()
        # TODO: Implement
        # system_information["free HDD space"] = free_HDD_space(install_folder_root)
        # TODO: Implement
        system_info["installed software"] = self._detect_installed_software()
        system_info["is Java installed"] = PCLOS.is_java_installed()

        # fmt: off
        # global _
        # if keep_logging_messages_in_english: _ = gettext.gettext  # switch lang
        # message = _(
        #     "WIP!\n"
        #     "Value returned: {} (type: {})"
        # ).format(system_information, type(system_information))
        # if keep_logging_messages_in_english: del _  # reset lang
        # fmt: on

        # logging.debug(message)
        return system_info

    def _detect_installed_software(self):
        # TODO: implement
        log.debug("WIP !" "Sending dummy data !!!")
        found_software = [
            ["OpenOffice", "2.0"],
            ["OpenOffice", "2.4", "pl", "gr"],
            ["LibreOffice", "3.0.0", "fr", "de"],
            ["LibreOffice", "7.5", "jp", "pl"],
            ["Clipart", "5.3"],
        ]
        log.debug(f"found_software: {found_software}")
        return found_software

    def _flags_logic(self) -> tuple[bool, list[dict[str, str]]]:
        """'Rises' flags indicating some operations will not be available

        This method performs checks of the operating system and
        sets the status of the flags in the self._flags object
        to TRUE if some package operations need to be BLOCKED.

        Returns
        -------
        tuple
          (any_limitations: bool, info_list: list of dicts)
          any_limitations is True if ANY flag was raised
          dict(s) in list contain(s) human readable reason(s) for rising
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
            info_list.append(
                {
                    "explanation": "Some package managers still running and "
                    "as a result you won't be able to install or uninstall "
                    "LibreOffice packages.\n"
                    "Advice: Close them and restart this program.\n"
                    "(Manager | PID)",
                    "data": running_managers,
                }
            )

        running_office_suits = PCLOS.get_running_Office_processes()
        if running_office_suits:  # an office app is running
            self.global_flags.block_removal = True
            self.global_flags.block_network_install = True
            self.global_flags.block_local_copy_install = True
            any_limitations = True
            info_list.append(
                {
                    "explanation": "Office is running and as a result you "
                    "won't be able to install or uninstall LibreOffice "
                    "packages.\n"
                    "Advice: Save your work, close Office and restart "
                    "this program.\n"
                    "(Office | PID)",
                    "data": running_office_suits,
                }
            )

        # no running manager prevents access to system rpm database
        if self.global_flags.block_checking_4_updates is False:
            check_successfull, is_updated = PCLOS.get_system_update_status()
            if is_updated is False:
                self.global_flags.block_network_install = True
                any_limitations = True
                if check_successfull:
                    info_list.append(
                        {
                            "explanation": "Uninstalled updates were detected "
                            "and as a result you won't be able to install "
                            "LibreOffice packages.\n"
                            "Advice: Update your system and restart "
                            "this program.",
                            "data": "",
                        }
                    )
                else:
                    info_list.append(
                        {
                            "explanation": "Failed to check update status "
                            "and as a result you won't be able to install "
                            "LibreOffice packages.\n"
                            "Advice: Check you internet connection "
                            "and restart this program.",
                            "data": "",
                        }
                    )

        if not PCLOS.is_lomanager2_latest(configuration.lomanger2_version):
            self.global_flags.block_network_install = True
            any_limitations = True
            info_list.append(
                {
                    "explanation": "You are running outdated version of "
                    "this program! "
                    "As a result you won't be able to install "
                    "LibreOffice packages.\n"
                    "Advice: Update your system and restart "
                    "this program.",
                    "data": "",
                }
            )

        return (any_limitations, info_list)

    # TODO: should this method be called with arguments
    #       at all or should it directly use attributes initialized
    #       in the MainLogic constructor?
    def _build_virtual_packages_list(self, software_list) -> None:
        """Builds a list of virtual packages based on installed ones."""
        for program in software_list:
            family = program[0]
            version = program[1]
            core_packages = VirtualPackage(
                "core-packages",
                family,
                version,
            )
            self._virtual_packages.append(core_packages)
            for lang in program[2:]:
                lang_package = VirtualPackage(lang, family, version)
                self._virtual_packages.append(lang_package)

    # TODO: should this method be called with arguments
    #       at all or should it directly use attributes initialized
    #       in the MainLogic constructor?
    def _build_latest_available_packages_list(
        self,
        latest_available_LO_version,
        latest_available_clipart_version,
    ) -> None:
        # TODO: Temporary, hard coded list of new LibreOffice packages
        #       and CLipart available for install from repo.
        #       (+ version of those 2 software components)
        # TODO: This list should be either generated automatically based
        #       on hard coded latest available versions, a fixed list of
        #       supported languages and file naming convention
        #       or read in from a pre generated configuration file.
        log.warning("Function not yet implemented. Sending fake data !!!")
        self._latest_available_packages = [
            VirtualPackage(
                "core-packages",
                "LibreOffice",
                latest_available_LO_version,
            ),
            VirtualPackage(
                "pl",
                "LibreOffice",
                latest_available_LO_version,
            ),
            VirtualPackage(
                "gr",
                "LibreOffice",
                latest_available_LO_version,
            ),
            VirtualPackage(
                "fr",
                "LibreOffice",
                latest_available_LO_version,
            ),
            VirtualPackage(
                "de",
                "LibreOffice",
                latest_available_LO_version,
            ),
            VirtualPackage(
                "jp",
                "LibreOffice",
                latest_available_LO_version,
            ),
            VirtualPackage(
                "it",
                "LibreOffice",
                latest_available_LO_version,
            ),
            VirtualPackage(
                "es",
                "LibreOffice",
                latest_available_LO_version,
            ),
            VirtualPackage(
                "core-packages",
                "Clipart",
                latest_available_clipart_version,
            ),
        ]
        pass

    def _install(
        self,
        virtual_packages,
        keep_packages,
        callback_function=None,
    ) -> dict:
        # TODO: This is dummy implementation for testing
        log.debug("WIP. This function sends fake data.")

        # Preparations
        current_progress_is = callback_function
        install_status = {
            "is_install_successful": False,
            "explanation": "Install procedure not executed.",
        }

        # 1 - Run collect_packages subprocedure
        packages_to_download = [p for p in virtual_packages if p.is_to_be_downloaded]
        log.debug(f"packages_to_download: {packages_to_download}")

        # TODO: Should it be a different function or perhaps
        #       callback_function should take some parameters other then
        #       integer representing percentage progress eg. a dictionary
        #       with information what progress is being reported:
        #       download, install, a what file etc..
        download_progress_callback = callback_function
        collect_status = self._collect_packages(
            packages_to_download,
            download_progress_callback,
        )

        if collect_status is False:
            message = "Failed to download all requested packages."
            install_status["explanation"] = message
            log.error(message)
            return install_status

        # At this point network_install and local_copy_install
        # procedures converge
        # 2) detect and terminate (kill -9) LibreOffice quickstarter
        self._terminate_LO_quickstarter()

        # 3) Run Java install procedure if needed
        for package in virtual_packages:
            if package.family == "Java":
                if package.is_marked_for_install:
                    java_install_status = self._install_Java()

                    if java_install_status is False:
                        message = "Failed to install Java."
                        install_status["explanation"] = message
                        log.error(message)
                        return install_status
                    else:  # All good, Java installed
                        break  # There can only ever be 1 Java virtual package

        # At this point everything needed is downloaded and verified
        # and Java is installed in the system.
        # We can remove old Office components
        # in preparation for the install step.
        # 4) Run Office uninstall procedure if needed
        packages_to_remove = [p for p in virtual_packages if p.is_marked_for_removal]
        log.debug(f"packages_to_remove: {packages_to_remove}")
        if packages_to_remove:  # Non empty list
            office_removal_status = self._office_uninstall(
                packages_to_remove,
                callback_function,
            )

            # If the procedure failed completely (no packages got uninstalled)
            # there is no problem - system state has not changed.
            # If however it succeeded but only partially this is a problem because
            # Office might have gotten corrupted and is no longer working and new
            # Office will not be installed. Recovery from such a condition is
            # likely to require manual user intervention - not good.
            # TODO: Can office_uninstall procedure be made to have dry-run option
            #       to make sure that uninstall is atomic (all or none)?
            if office_removal_status is False:
                message = "Failed to remove Office components."
                install_status["explanation"] = message
                log.error(message)
                return install_status

        # 5) Run Office install procedure if needed
        packages_to_install = [
            p
            for p in virtual_packages
            if (p.is_marked_for_install or p.is_marked_for_upgrade)
        ]
        log.debug(f"packages_to_install: {packages_to_install}")
        if packages_to_install:  # Non empty list
            office_install_status = self._install_LibreOffice(
                packages_to_install,
                callback_function,
            )

            if office_install_status is False:
                message = "Failed to install Office components."
                install_status["explanation"] = message
                log.error(message)
                return install_status

        # 6) Any Office base package was affected ?
        # TODO: Can this be done better ?
        for package in packages_to_install:
            if package.kind == "core-packages" and package.family == "LibreOffice":
                self._disable_LO_update_checks()
                self._add_templates_to_etcskel()
        for package in packages_to_remove:
            if package.kind == "core-packages" and package.family == "LibreOffice":
                self._clean_dot_desktop_files()

        # 7) Should downloaded packages be removed ?
        log.debug(f"keep_packages = {keep_packages}")
        if keep_packages is True:
            log.debug(
                f"Manually setting <<offline_copy_folder>> to <</tmp/LO_saved_packages>>!"
            )
            offline_copy_folder = "/tmp/LO_saved_packages"
            self._save_copy_for_offline_install(offline_copy_folder)

        # 8) clean up temporary files
        self._clean_tmp_folder()

        message = "All packages successfully installed"
        install_status["is_install_successful"] = True
        install_status["explanation"] = message
        log.info(message)
        return install_status

    def _collect_packages(self, packages_to_download: list, callback_function) -> bool:
        log.debug("WIP. This function sends fake data.")
        # Preparations
        tmp_directory = configuration.tmp_directory

        is_every_package_collected = False

        log.debug(f"Packages to download: {packages_to_download}")
        log.debug("Collecting packages...")
        time.sleep(2)
        log.debug("...done collecting packages.")

        is_every_package_collected = True
        return is_every_package_collected

    def _terminate_LO_quickstarter(self):
        log.debug("WIP. This function sends fake data.")

        log.debug("Checking for LibreOffice quickstarter process...")
        log.debug("LibreOffice quickstarter is running (PID: ABCD)")
        log.debug("Terminating LibreOffice quickstarter...")
        time.sleep(2)
        log.debug("...done.")

    def _install_Java(self) -> bool:
        log.debug("WIP. This function sends fake data.")

        is_java_successfully_installed = False
        log.info("Starting Java install procedure...")

        time.sleep(2)

        is_java_successfully_installed = True
        log.info("Java successfully installed.")

        return is_java_successfully_installed

    def _office_uninstall(
        self,
        packages_to_remove: list,
        callback_function,
    ) -> bool:
        log.debug("WIP. This function sends fake data.")

        is_every_package_successfully_removed = False
        log.debug(f"Packages to remove: {packages_to_remove}")
        log.info("Removing packages...")

        time.sleep(2)

        is_every_package_successfully_removed = True
        log.info("...done removing packages.")

        return is_every_package_successfully_removed

    def _install_LibreOffice(
        self,
        packages_to_install: list,
        callback_function,
    ) -> bool:
        log.debug("WIP. This function sends fake data.")
        # TODO: naming
        current_progress_is = callback_function

        is_every_package_successfully_installed = False
        log.debug(f"Packages to install: {packages_to_install}")
        log.info("Installing packages...")

        total_time_sek = 5
        steps = 30
        for i in range(steps):
            progress = int((i / (steps - 1)) * 100)  # progress in % (0-100)
            time.sleep(total_time_sek / steps)

            # report progress
            # # directly to log
            log.info(f"install progress: {progress}%")
            # # using callback if available (emitting Qt signal)
            if callback_function is not None:
                current_progress_is(progress)

        is_every_package_successfully_installed = True
        log.info("...done installing packages.")

        return is_every_package_successfully_installed

    def _disable_LO_update_checks(self):
        log.debug("WIP. This function sends fake data.")

        log.debug("Preventing LibreOffice from looking for updates on its own...")
        time.sleep(1)
        log.debug("...done.")

    def _add_templates_to_etcskel(self):
        # TODO: This function should put a file (smth.xcu) to /etc/skel
        #       in order to have LO properly set up for any new user
        #       accounts created in the OS
        log.debug("WIP. This function sends fake data.")

        log.debug("Adding files to /etc/skel ...")
        time.sleep(1)
        log.debug("...done.")

    def _clean_dot_desktop_files(self):
        # TODO: This function should remove association between LibreOffice
        #       and Open Document file formats (odt, odf, etc.) from the
        #       global .desktop file (and user files too?)
        log.debug("WIP. This function sends fake data.")

        log.debug("Rebuilding menu entries...")
        time.sleep(1)
        log.debug("...done.")

    def _save_copy_for_offline_install(self, target_folder):
        # TODO: This function should put all files needed for offline
        #       installation in a structured way into the target_folder
        log.debug("WIP. This function sends fake data.")

        log.debug("Saving files for offline install...")
        time.sleep(1)
        log.debug("...done.")

    def _clean_tmp_folder(self):
        # TODO: This function should remove all files from tmp_directory.
        log.debug("WIP. This function sends fake data.")

        # Preparations
        tmp_directory = configuration.tmp_directory

        log.debug("Cleaning temporary files...")
        time.sleep(1)
        log.debug("...done.")

    def _local_copy_install_procedure(
        self,
        virtual_packages,
        local_copy_directory,
        callback_function=None,
    ) -> dict:
        # TODO: This is dummy implementation for testing
        log.debug("WIP !")

        # Preparations

        current_progress_is = callback_function
        install_status = {
            "is_install_successful": False,
            "explanation": "Install procedure not executed.",
        }

        # Perform rough verification of local copy directory
        is_Java_present = False
        is_LibreOffice_core_present = False
        is_LibreOffice_lang_present = False
        is_Clipart_present = False
        # local_copy_directory exists?
        if pathlib.Path(local_copy_directory).is_dir():
            (
                is_Java_present,
                is_LibreOffice_core_present,
                is_LibreOffice_lang_present,
                is_Clipart_present,
            ) = self._verify_local_copy(local_copy_directory)
        else:
            message = "Could not find directory with saved packages."
            install_status["explanation"] = message
            log.error(message)
            return install_status

        # Mark virtual packages accordingly to the
        # content of local_copy_directory and system state
        if is_LibreOffice_core_present is False:
            # There are no LibreOffice core packages in local_copy_directory but
            # perhaps the user meant to install Openclipart library?
            if is_Clipart_present is False:
                message = (
                    "Neither LibreOffice nor Openclipart library were found "
                    "in the folder provided."
                )
                install_status["explanation"] = message
                log.error(message)
                return install_status
            else:  # Clipart packages found in local_copy_directory
                # FIXME: Currently there is no guarantee clipart virtual package
                #       will be in virtual_packages.
                #       This is a problem and must be fixed in PackageMenu
                #       And what if it exists? Should it be upgraded ?
                log.debug("Openclipart rpms found and marked for installation.")
                for package in virtual_packages:
                    if package.family == "Clipart":
                        package.is_marked_for_removal = False
                        package.is_marked_for_upgrade = False
                        package.is_marked_for_install = True
                        package.is_to_be_downloaded = False

        if is_LibreOffice_core_present is True:
            # Assuming user wants to install LibreOffice from local_copy_directory.
            # This is possible only if Java is present in the OS or
            # can be installed from local_copy_directory
            if PCLOS.is_java_installed() is False and is_Java_present is False:
                message = (
                    "Java is not installed in the system and was not be found in "
                    "the directory provided."
                )
                install_status["explanation"] = message
                log.error(message)
                return install_status
            elif PCLOS.is_java_installed() is False and is_Java_present is True:
                # Java not installed but can be installed from local_copy_directory
                # FIXME: Java virtual package in not guaranteed to exist in
                #        virtual_packages. FIX this.
                log.debug("Java rpms found and marked for installation.")
                for package in virtual_packages:
                    if package.family == "Java":
                        package.is_marked_for_removal = False
                        package.is_marked_for_upgrade = False
                        package.is_marked_for_install = True
                        package.is_to_be_downloaded = False

            elif PCLOS.is_java_installed() is True and is_Java_present is False:
                log.debug("Java already installed.")
                for package in virtual_packages:
                    if package.family == "Java":
                        package.is_marked_for_removal = False
                        package.is_marked_for_upgrade = False
                        package.is_marked_for_install = False
                        package.is_to_be_downloaded = False
            else:
                # TODO Java is installed AND is present in local_copy_directory
                #      what should be done it such a case? Reinstall?
                #      Try using rpm -Uvh which will update it if package is newer?
                #      Skipping for now.
                pass

            log.debug(
                "Marking all existing OpenOffice and LibreOffice packages for removal."
            )
            for package in virtual_packages:
                if package.family == "OpenOffice" or package.family == "LibreOffice":
                    package.is_marked_for_removal = True
                    package.is_marked_for_upgrade = False
                    package.is_marked_for_install = False
                    package.is_to_be_downloaded = False

            log.debug("Marking LibreOffice core for install.")
            # FIXME: Which package to mark? virtual_packages only contains
            #        list of installed packages (which by itself should be changes
            #        for different reason) and the version number of the
            #        LO core in the local_copy_directory is unknown.
            #        Parse the filename? add "0.0.0.0" as indicating local copy
            #        install?
            for package in virtual_packages:
                if package.family == "OpenOffice" and package.kind == "core-packages":
                    package.is_marked_for_removal = False
                    package.is_marked_for_upgrade = False
                    package.is_marked_for_install = True
                    package.is_to_be_downloaded = False

            log.debug("DO SOMETHING HERE")
            if is_LibreOffice_lang_present:
                # User has also saved some language packs. Install them all.
                # TODO: mark them for install but not for download
                # FIXME: Again which packages to mark? virtual_packages only contains
                #        list of installed packages (which by itself should be changes
                #        for different reason) and the version number of the
                #        LO core in the local_copy_directory is unknown.
                #        Parse the filename? add "0.0.0.0" as indicating local copy
                #        install?
                log.debug("DO SOMETHING HERE")
            if is_Clipart_present:
                # User has also saved clipart package. Install it.
                # TODO: mark clipart for installation/upgrade accordingly
                # FIXME: Again which package to mark? virtual_packages only contains
                #        list of installed packages (which by itself should be changes
                #        for different reason) and the version number of the
                #        LO core in the local_copy_directory is unknown.
                #        Parse the filename? add "0.0.0.0" as indicating local copy
                #        install?
                log.debug("DO SOMETHING HERE")

        # TODO: should it now converge with the network_install procedure ?

        return install_status

    def _verify_local_copy(
        self,
        local_copy_directory: str,
    ) -> tuple[bool, bool, bool, bool]:
        """Checks for presence of saved packages based on file name convention

        Functions checks for:
            - 2 Java rpm packages
            - any LibreOffice core package
            - LibreOffice langs/help packs folder
            - 2 clipart rpm packages
        based on their expected files names (No version checking is performed).
        Returned is True/False for every of above 4 components.
        True means component can be installed from local_copy_directory.

        Parameters
        ----------
        local_copy_directory : str
          Directory containing saved packages

        Returns
        -------
        tuple[bool,bool,bool,bool]
          (T) for each: Java, LibreOffice core, LibreOffice langs, Clipart if
          suitable for install from local_copy_directory (F) otherwise
        """

        log.debug("WIP")

        is_Java_present = False
        is_LibreOffice_core_present = False
        is_LibreOffice_lang_present = False
        is_Clipart_present = False

        log.debug("Verifying local copy ...")
        # 1) Directory for Java rpms exist inside?
        # (Java_RPMS as directory name is set here as a standard)
        Java_dir = pathlib.Path(local_copy_directory).joinpath("Java_RPMS")
        log.debug(f"Java RPMS dir: {Java_dir}")
        if Java_dir.is_dir():
            # Files: task-java-<something>.rpm ,  java-sun-<something>.rpm
            # are inside? (no specific version numbers are assumed or checked)
            is_task_java_present = any(
                ["task-java" in file.name for file in Java_dir.iterdir()]
            )
            is_java_sun_present = any(
                ["java-sun" in file.name for file in Java_dir.iterdir()]
            )
            # Only if both are present we conclude Java can be installed
            # from the local copy directory.
            is_Java_present = all([is_task_java_present, is_java_sun_present])

        # 2) LibreOffice core packages folder
        LO_core_dir = pathlib.Path(local_copy_directory).joinpath("LO_core_TGZS")
        if LO_core_dir.is_dir():
            # Check for tar.gz archive with core packages
            regex = re.compile(
                "LibreOffice_[0-9]*.[0-9]*.[0-9]*_Linux_x86-64_rpm.tar.gz"
            )
            is_LibreOffice_core_present = any(
                [regex.search(file.name) for file in LO_core_dir.iterdir()]
            )

        # 3) LibreOffice lang and help packages folder
        #    (its content is not critical for the decision procedure
        #     so just check if it exists and is non empty)
        LO_lang_dir = pathlib.Path(local_copy_directory).joinpath("LO_lang_TGZS")
        is_LibreOffice_lang_present = LO_lang_dir.is_dir() and any(
            LO_lang_dir.iterdir()
        )

        # 4) Clipart directory
        Clipart_dir = pathlib.Path(local_copy_directory).joinpath("Clipart_RPMS")
        if Clipart_dir.is_dir():
            # Files: libreoffice-openclipart-<something>.rpm ,
            # clipart-openclipart-<something>.rpm
            # are inside? (no specific version numbers are assumed or checked)
            is_lo_clipart_present = any(
                [
                    "libreoffice-openclipart" in file.name
                    for file in Clipart_dir.iterdir()
                ]
            )
            is_openclipart_present = any(
                ["clipart-openclipart" in file.name for file in Clipart_dir.iterdir()]
            )
            # Only if both are present clipart library can be installed
            # from the local copy directory.
            is_Clipart_present = all([is_lo_clipart_present, is_openclipart_present])

        log.debug(f"Java is present: {is_Java_present}")
        log.debug(f"LO core is present: {is_LibreOffice_core_present}")
        log.debug(f"LO langs is present: {is_LibreOffice_lang_present}")
        log.debug(f"Clipart lib is present: {is_Clipart_present}")
        return (
            is_Java_present,
            is_LibreOffice_core_present,
            is_LibreOffice_lang_present,
            is_Clipart_present,
        )

    # -- end Private methods of MainLogic


class PackageMenu(object):
    def __init__(
        self,
        packages: list[VirtualPackage],
        l_aval_pcks: list[VirtualPackage],
        l_aval_LO_ver: str,
        l_aval_clipart_ver: str,
    ) -> None:
        # TODO: Refactor these variables. In fact there is no need
        #       to make any intermediate ones, just name the
        #       arguments properly and get rid of "self."
        self.latest_available_LO_version = l_aval_LO_ver
        self.latest_available_clipart_version = l_aval_clipart_ver
        self.latest_available_packages = l_aval_pcks

        # Object representing items in the menu
        self.packages = packages

        # A dictionary of packages to alter
        self.package_delta = {
            "packages_to_remove": [],
            "space_to_be_freed": 0,
            "packages_to_install": [],
            "space_to_be_used": 0,
        }

        # Set initial state of the menu by analyzing package
        # dependencies and system state to decide
        # what the user can/cannot do.
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
            if (
                package.is_remove_opt_visible
                and package.is_remove_opt_enabled
                and package.is_removable
            ):
                is_logic_applied = self._apply_removal_logic(package, value)
            else:
                is_logic_applied = False
                raise PermissionError(
                    "It's not permited to mark/unmark this package for removal"
                )
        elif column == 4:
            if (
                package.is_upgrade_opt_visible
                and package.is_upgrade_opt_enabled
                and package.is_upgradable
            ):
                is_logic_applied = self._apply_upgrade_logic(package, value)
            else:
                is_logic_applied = False
                raise PermissionError(
                    "It's not permited to mark/unmark this package for upgrade"
                )
        elif column == 5:
            if (
                package.is_install_opt_visible
                and package.is_install_opt_enabled
                and package.is_installable
            ):
                is_logic_applied = self._apply_install_logic(package, value)
            else:
                is_logic_applied = False
                raise PermissionError(
                    "It's not permited to mark/unmark this package for install"
                )
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
                for real_package in package.real_packages:
                    size += real_package["size"]
                    self.package_delta["packages_to_remove"] += [
                        real_package["rpm name"]
                    ]
                self.package_delta["space_to_be_freed"] = size
            if package.is_marked_for_install:
                size = 0
                for real_package in package.real_packages:
                    size += real_package["size"]
                    self.package_delta["packages_to_install"] += [
                        real_package["rpm name"]
                    ]
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

        is_apply_install_successul = False

        # OpenOffice dependency tree
        if package.family == "OpenOffice":
            # OpenOffice is not supported and can never be installed
            # by this program - it can only be removed.
            # The code here should never execute.
            is_apply_install_successul = False
            raise NotImplementedError(
                "OpenOffice cannot be installed, it can only be uninstalled."
            )

        # LibreOffice dependency tree
        if package.family == "LibreOffice":
            # unmarking the request for install
            if mark is False:
                # 1) unmark yourself
                package.is_marked_for_install = False
                # 2) If this is the request to unmark the last of all
                #    new lang packs marked for install (user changes mind
                #    and decides not to install any new languages) -
                #    allow to uninstall existing (is exists) core-packages.
                if package.kind != "core-packages":
                    langs_left = []
                    for candidate in self.packages:
                        if (
                            candidate.family == "LibreOffice"
                            and candidate.version == package.version
                            and candidate.kind != "core-packages"
                            and candidate.is_installable is True
                            and candidate.is_marked_for_install is True
                        ):
                            langs_left.append(candidate)

                    if not langs_left:
                        for candidate in self.packages:
                            if (
                                candidate.family == "LibreOffice"
                                and candidate.version == package.version
                                and candidate.kind == "core-packages"
                            ):
                                candidate.is_remove_opt_enabled = True
                # 3) If this IS the core-packages
                #    don't leave your lang packs hanging - unmark them
                if package.kind == "core-packages":
                    for candidate in self.packages:
                        if (
                            candidate.family == "LibreOffice"
                            and candidate.version == package.version
                            and candidate.kind != "core-packages"
                        ):
                            candidate.is_marked_for_install = False
                        # 4) Unmark the removal field of any OpenOffice to
                        #    prevent the case when the user changes mind
                        #    and unmarks LibreOffice install but
                        #    OpenOffice that was marked for uninstall
                        #    (in the "requesting install" case below) stays
                        #    marked and gets accidentally removed leaving
                        #    the user with NO Office installed at all.
                        #    This can be done ONLY IF no LibreOffice package
                        #    is left marked for install. That is only after
                        #    the last LibreOffice package that was marked
                        #    for install gets unmarked - and this happens here
                        #    automatically when the core-packages
                        #    gets unmarked.
                        if candidate.family == "OpenOffice":
                            candidate.is_marked_for_removal = False
                            candidate.is_remove_opt_enabled = True
                is_apply_install_successul = True

            # requesting install
            if mark is True:
                # 1) mark yourself for install
                package.is_marked_for_install = True
                # 2) If this is a lang pack
                #    mark your parent (core-packages) as well
                if package.kind != "core-packages":
                    for candidate in self.packages:
                        if (
                            candidate.family == "LibreOffice"
                            and candidate.version == package.version
                            and candidate.kind == "core-packages"
                        ):
                            # core-packages already installed - prevent
                            # it's removal
                            if candidate.is_removable is True:
                                candidate.is_remove_opt_enabled = False
                            # core-packages not installed - mark for install
                            else:
                                candidate.is_marked_for_install = True
                # 3) mark any OpenOffice for removal
                #    and set is_remove_opt_enabled to False
                for candidate in self.packages:
                    if candidate.family == "OpenOffice":
                        candidate.is_marked_for_removal = True
                        candidate.is_remove_opt_enabled = False
                # 4)  As the install option is only available
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

        is_apply_removal_successul = False

        # OpenOffice dependency tree
        if package.family == "OpenOffice":
            # unmarking the request for removal
            if mark is False:
                # If the users wants to unmark the removal of an OpenOffice
                # (previously marked for removal) for whatever reason
                # this should be allowed BUT:
                # Since the OpenOffice is not supported and this is
                # LibreOffice Manager not OpenOffice Manager there are
                # only 2 options:
                # - keep OpenOffice and not install LibreOffice at all
                # - or completely remove ANY and ALL OpenOffice packages
                # This program will not allow for any partial marking of
                # OpenOffice packages.
                for candidate in self.packages:
                    if candidate.family == "OpenOffice":
                        candidate.is_marked_for_removal = False
                is_apply_removal_successul = True

            # requesting removal
            if mark is True:
                # In case the user marks ANY OpenOffice package for removal
                # it's a good opportunity to get rid of all OpenOffice
                # packages since this suite is NOT SUPPORTED
                for markpackege in self.packages:
                    if markpackege.family == "OpenOffice":
                        markpackege.is_marked_for_removal = True
                is_apply_removal_successul = True

        # LibreOffice dependency tree
        if package.family == "LibreOffice":
            # unmarking the request for removal
            if mark is False:
                # If the users wants to unmark the removal of an LibreOffice
                # package previously marked for removal (for whatever reason)
                # this should be allowed BUT:
                # - it should not lead (by marking and unmarking core-packages)
                #   to lang packs left without their core-packages.
                # - the install option for new lang packs should re-enabled
                package.is_marked_for_removal = False
                if package.kind == "core-packages":
                    for candidate in self.packages:
                        if (
                            candidate.kind != "core-packages"
                            and candidate.family == "LibreOffice"
                            and candidate.version == package.version
                        ):
                            candidate.is_marked_for_removal = False
                            if candidate.is_installable:
                                candidate.is_install_opt_enabled = True
                is_apply_removal_successul = True

            # requesting removal of ...
            if mark is True:
                # ... a LibreOffice core-packages
                if package.kind == "core-packages":
                    # mark yourself for removal
                    package.is_marked_for_removal = True
                    #  mark all your children (lang packages) for removal too
                    for candidate in self.packages:
                        if (
                            candidate.kind != "core-packages"
                            and candidate.family == "LibreOffice"
                            and candidate.version == package.version
                        ):
                            candidate.is_marked_for_removal = True
                    # prevent installation of any new lang packs
                    for candidate in self.packages:
                        if (
                            candidate.kind != "core-packages"
                            and candidate.family == "LibreOffice"
                            and candidate.version == package.version
                            and candidate.is_installable is True
                        ):
                            candidate.is_marked_for_install = False
                            candidate.is_install_opt_enabled = False
                # ... any lang package
                else:
                    # only mark yourself for removal
                    package.is_marked_for_removal = True
                is_apply_removal_successul = True

        # Clipart dependency tree
        if package.family == "Clipart":
            # As this is an independent package no special logic is needed,
            # just mark the package as requested.
            package.is_marked_for_removal = mark
            is_apply_removal_successul = True

        return is_apply_removal_successul

    def _apply_upgrade_logic(self, package: VirtualPackage, mark: bool):
        """Marks package for upgrade changing flags of other packages accordingly

        This procedure will mark requested package for upgrade and make
        sure this causes other packages to be also upgraded or prevented
        from being removed respecting dependencies.

        Parameters
        ----------
        package : VirtualPackage

        mark : bool
          True - mark for upgrade, False - unmark (give up upgrading)

        Returns
        -------
        bool
          True if packages upgrade logic was applied successfully,
          False otherwise
        """

        is_apply_upgrade_successul = False

        # OpenOffice dependency tree
        if package.family == "OpenOffice":
            # OpenOffice is not supported and can never be upgraded
            # by this program - it can only be removed.
            # The code here should never execute.
            is_apply_upgrade_successul = False
            raise NotImplementedError(
                "OpenOffice cannot be upgraded, it can only be uninstalled."
            )

        # LibreOffice dependency tree
        if package.family == "LibreOffice":
            # unmarking the request for upgrade
            if mark is False:
                # TODO: Unmark any removals of ANY Office. This is to prevent
                #       the situation when unmarking the (already marked)
                #       upgrade options leaves existing Office suit(s)
                #       marked for removal. Then accidental "Apply Changes"
                #       would lead to all existing office suits getting
                #       uninstalled and latest office not installed.
                for candidate in self.packages:
                    if (
                        candidate.family == "OpenOffice"
                        or candidate.family == "LibreOffice"
                    ):
                        candidate.is_marked_for_removal = False
                        candidate.is_remove_opt_enabled = True
                #  unmark yourself
                package.is_marked_for_upgrade = False
                # 4b)   Upgrade is atomic -- all or none so:
                #       unmark for upgrade other packages in the same tree
                #       (parent or children or sibling(s))
                #       BUT only those that were marked as upgradable
                for candidate in self.packages:
                    if (
                        candidate is not package
                        and candidate.family == "LibreOffice"
                        and candidate.version == package.version
                        and candidate.is_upgradable
                    ):
                        candidate.is_marked_for_upgrade = False
                is_apply_upgrade_successul = True

            # requesting upgrade
            if mark is True:
                # 1a) mark ALL OpenOffice packages installed for removal
                # 1b)   and their remove_opt_enabled to False
                for candidate in self.packages:
                    if candidate.family == "OpenOffice":
                        candidate.is_marked_for_removal = True
                        candidate.is_remove_opt_enabled = False
                # 2a) mark installed LibreOffice versions other then
                #     newest installed for removal
                # 2b)   and their remove_opt_enabled to False
                for candidate in self.packages:
                    if (
                        candidate.family == "LibreOffice"
                        and candidate.version != self.newest_installed_LO_version
                    ):
                        candidate.is_marked_for_removal = True
                        candidate.is_remove_opt_enabled = False
                    # 3a) Do not mark newest installed LO for removal. Just
                    #     mark its remove_opt_enabled as False
                    #     (disable explicit removal request)
                    #     This will show the latest is not removed but upgraded
                    # 3b)
                    if (
                        candidate.family == "LibreOffice"
                        and candidate.version == self.newest_installed_LO_version
                    ):
                        candidate.is_remove_opt_enabled = False
                # 4a) mark yourself for upgrade
                package.is_marked_for_upgrade = True
                # 4b)   Upgrade is atomic -- all or none so:
                #       mark for upgrade other packages in the same tree
                #       (parent or children or sibling(s))
                #       BUT only those that were marked as upgradable
                for candidate in self.packages:
                    if (
                        candidate is not package
                        and candidate.family == "LibreOffice"
                        and candidate.version == package.version
                        and candidate.is_upgradable
                    ):
                        candidate.is_marked_for_upgrade = True
                is_apply_upgrade_successul = True

        # Clipart dependency tree
        if package.family == "Clipart":
            # unmarking the request for upgrade
            if mark is False:
                # unmark yourself
                package.is_marked_for_upgrade = False
                # The user changed his mind and is unmarking update so:
                # - unmarked removal of existing clipart package
                # - allow manual marking of its removal
                package.is_marked_for_removal = False
                package.is_remove_opt_enabled = True
                is_apply_upgrade_successul = True

            # requesting upgrade
            if mark is True:
                # mark yourself
                # TODO: should it be also marked_for_removal ?
                package.is_remove_opt_enabled = False
                package.is_marked_for_upgrade = True
                is_apply_upgrade_successul = True

        return is_apply_upgrade_successul

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
            log.debug(f"Newest installed LO: {self.newest_installed_LO_version}")
            # b) latest version already installed
            if self.newest_installed_LO_version == self.latest_available_LO_version:
                log.debug("Your LO is already at latest available version")
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
