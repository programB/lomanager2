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
import logging

from i18n import _

from .datatypes import VirtualPackage

log = logging.getLogger("lomanager2_logger")


class ManualSelectionLogic(object):
    def __init__(
        self,
        root_node: VirtualPackage,
        latest_Java_version: str,
        newest_Java_version: str,
        recommended_LO_version: str,
        newest_installed_LO_version: str,
        recommended_Clipart_version: str,
        newest_Clipart_version: str,
    ) -> None:
        self.recommended_LO_version = recommended_LO_version
        self.recommended_clipart_version = recommended_Clipart_version
        self.newest_installed_LO_version = newest_installed_LO_version

        self.root = root_node

        self.info_to_install = []
        self.info_to_remove = []

    # -- Public interface for ManualSelectionLogic
    def apply_install_logic(self, package: VirtualPackage, mark: bool):
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

        log.debug(_(">>> Install logic triggered  package: {} <<<").format(package))

        is_apply_install_successful = False

        java_pkgs = [c for c in self.root.children if "Java" in c.family]
        java = None if not java_pkgs else java_pkgs[0]

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
                    siblings = package.get_siblings()
                    is_any_sibling_marked_for_install = any(
                        [s for s in siblings if s.is_marked_for_install]
                    )
                    if (
                        not is_any_sibling_marked_for_install
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
                #    the recommended version
                #    make the removal option for installed Office
                #    accessible again
                if package.version == self.recommended_LO_version:
                    family_members = package.get_your_family()
                    is_any_member_marked_for_install = any(
                        [m for m in family_members if m.is_marked_for_install]
                    )
                    if not is_any_member_marked_for_install and java is not None:
                        for office in java.children:
                            if office.version != self.recommended_LO_version:
                                office.is_remove_opt_enabled = True
                                for lang in office.children:
                                    lang.is_remove_opt_enabled = True
                is_apply_install_successful = True

            # requesting install
            if mark is True:
                # 1) mark yourself for install
                package.is_marked_for_install = True
                # 2) Java not installed - install it
                if java is not None and not java.is_installed:
                    java.is_marked_for_install = True
                # 3) if installing recommended LO mark older versions for removal
                if java is not None and package.version == self.recommended_LO_version:
                    for office in java.children:
                        if office.version != self.recommended_LO_version:
                            office.mark_for_removal()
                            office.is_remove_opt_enabled = False
                            for lang in office.children:
                                lang.mark_for_removal()
                                lang.is_remove_opt_enabled = False
                                if lang.is_installed:
                                    for item in package.get_your_family():
                                        if item.is_langpack() and item.kind == lang.kind:
                                            item.is_marked_for_install = True
                # 4) If this is a lang pack
                if package.is_langpack():
                    if package.parent is not None:
                        if package.parent.is_installed:
                            # prevent installed parent getting removed
                            package.parent.is_remove_opt_enabled = False
                        else:
                            # parent not installed - install it as well
                            package.parent.is_marked_for_install = True
                is_apply_install_successful = True

        # Clipart dependency tree
        if package.family == "Clipart":
            # mark yourself
            package.is_marked_for_install = mark
            #
            if package.version == self.recommended_clipart_version:
                for child in self.root.children:
                    if (
                        child.family == "Clipart"
                        and child.version != self.recommended_clipart_version
                    ):
                        if mark is True:
                            # if installing recommended version mark
                            # other versions for removal
                            child.mark_for_removal()
                            child.is_remove_opt_enabled = False
                        else:
                            # if unmarking the recommended version
                            # make the removal option for installed
                            # one accessible again
                            child.is_remove_opt_enabled = True
            is_apply_install_successful = True

        self._decide_what_to_download()
        self._update_changes_info()
        return is_apply_install_successful

    def apply_removal_logic(self, package: VirtualPackage, mark: bool) -> bool:
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

        log.debug(_(">>> Removal logic triggered  package: {} <<<").format(package))

        is_apply_removal_successful = False

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
                is_apply_removal_successful = True

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
                is_apply_removal_successful = True

        # Clipart dependency tree
        if package.family == "Clipart":
            # mark the package as requested.
            package.is_marked_for_removal = mark
            is_apply_removal_successful = True

        self._decide_what_to_download()
        self._update_changes_info()
        return is_apply_removal_successful

    # -- end Public interface for ManualSelectionLogic

    # -- Private methods of ManualSelectionLogic
    def _decide_what_to_download(self):
        # Never keep the reference to package list
        packages = []
        self.root.get_subtree(packages)
        packages.remove(self.root)
        for package in packages:
            # if package.is_marked_for_install and package.is_installed is False:
            if package.is_marked_for_install and package.is_installed is False:
                package.is_marked_for_download = True
            else:
                package.is_marked_for_download = False

    def _update_changes_info(self):
        def pretty_name(package):
            if package.is_langpack():
                return (
                    package.family
                    + " "
                    + package.version
                    + _(" language: ")
                    + package.kind
                )
            else:
                return package.family + " " + package.version + " core"

        # Never keep the reference to package list
        packages = []
        self.root.get_subtree(packages)
        packages.remove(self.root)
        self.info_to_install = [
            pretty_name(p) for p in packages if p.is_marked_for_install
        ]
        self.info_to_remove = [
            pretty_name(p) for p in packages if p.is_marked_for_removal
        ]

    # -- end Private methods of ManualSelectionLogic
