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
import signal
import socket
import sys

from applogic.packagelogic import MainLogic
from qtinterface.delegates import columns
from qtinterface.gui import AppMainWindow
from qtinterface.pysidecompat import *
from qtinterface.threads import ProcedureWorker
from qtinterface.viewmodels import (ClipartMenuRenderModel,
                                    LanguageMenuRenderModel,
                                    OfficeMenuRenderModel, SoftwareMenuModel)

from i18n import _
from defs import __version__

log = logging.getLogger("lomanager2_logger")


class Adapter(QObject):
    # Register custom signals
    progress_description_signal = Signal(str)
    progress_signal = Signal(int)
    overall_progress_description_signal = Signal(str)
    overall_progress_signal = Signal(int)
    rebuild_tree_signal = Signal()
    thread_worker_ready_signal = Signal()
    warnings_awaiting_signal = Signal(list)
    check_system_state_signal = Signal()
    is_GUI_locked_signal = Signal(bool)

    def __init__(self, app_logic, main_view) -> None:
        super().__init__()

        # Application's logic
        self._app_logic = app_logic

        # Model (transforms data from app logic to a form digestible by views)
        self._software_menu_model = SoftwareMenuModel(
            self._app_logic,
            column_names=[columns[col]["i18n_name"] for col in columns],
        )

        # Views
        self._app_main_view = main_view

        self._office_view = self._app_main_view.office_view
        self._clipart_view = self._app_main_view.clipart_view

        self._langs_view = self._app_main_view.extra_langs_window.langs_view
        self._progress_view = self._app_main_view.progress_dialog
        self._info_view = self._app_main_view.info_dialog
        self._apply_changes_view = self._app_main_view.confirm_apply_dialog
        self._local_copy_view = self._app_main_view.confirm_local_copy_dialog

        # Render models (further filter/condition data before sending to views)
        self._office_menu_rendermodel = OfficeMenuRenderModel(
            model=self._software_menu_model, parent=self._office_view
        )
        self._clipart_menu_rendermodel = ClipartMenuRenderModel(
            model=self._software_menu_model, parent=self._clipart_view
        )
        self._language_menu_rendermodel = LanguageMenuRenderModel(
            model=self._software_menu_model, parent=self._langs_view
        )

        self._bind_views_to_models()
        self._connect_signals_and_slots()
        self._preset_views()

    def _bind_views_to_models(self):
        self._office_view.setModel(self._office_menu_rendermodel)
        self._clipart_view.setModel(self._clipart_menu_rendermodel)
        self._langs_view.setModel(self._language_menu_rendermodel)

    def _connect_signals_and_slots(self):
        # Option available to the user: Select additional language packs
        self._app_main_view.actionAddLanguages.triggered.connect(self._add_langs)

        # Option available to the user: Apply selected changes
        self._app_main_view.actionApplyChanges.triggered.connect(self._apply_changes)

        # Option available to the user: Install from local copy
        self._app_main_view.actionInstallFromLocalCopy.triggered.connect(
            self._install_from_local_copy
        )

        # Option available to the user: Open help window
        self._app_main_view.actionHelp.triggered.connect(self._show_docs)

        # Option available to the user: Open help window
        self._app_main_view.actionAbout.triggered.connect(self._show_about)

        # Option available to the user: Quit the app
        self._app_main_view.actionQuit.triggered.connect(self._cleanup_and_exit)

        # Internal signal: Ask applogic to redo package tree from scratch
        self.rebuild_tree_signal.connect(self._rebuild_tree)

        # Internal signal: Lock/Unlock GUI elements
        self.is_GUI_locked_signal.connect(self._GUI_locks)

        # Internal signal: Start already prepared thread worker
        self.thread_worker_ready_signal.connect(self._thread_start)

        # Internal signal: Show dialog with messages produced by applogic
        self.warnings_awaiting_signal.connect(self._warnings_show)

        # Internal signal: Check OS state; show progress dialog while checking
        self.check_system_state_signal.connect(self._check_system_state)

    def _preset_views(self):
        """Any extra changes to appearance of views not done by render models"""
        for n, column_flags in enumerate(columns.values()):
            if column_flags.get("show_in_software_view") is False:
                self._office_view.hideColumn(n)
                self._clipart_view.hideColumn(n)
            if column_flags.get("show_in_langs_view") is False:
                self._langs_view.hideColumn(n)

    def _rebuild_tree(self):
        log.debug(_("Starting package tree rebuild!"))
        self._app_logic.rebuild_package_tree()
        # Inform model that underlying data source has finished changing
        # (corresponding beginResetModel is in the _thread_start)
        self._software_menu_model.endResetModel()
        # Have the model inform all attached views to redraw themselves entirely
        self._software_menu_model.layoutChanged.emit()
        # Check if there are any messages that should be shown to the user
        if self._app_logic.warnings:
            self.warnings_awaiting_signal.emit(self._app_logic.get_warnings())

    def _add_langs(self):
        self._app_main_view.extra_langs_window.exec()

    def _show_docs(self):
        self._app_main_view.docs_dialog.show()

    def _show_about(self):
        about_text = _(
            "LibreOffice Manager 2 (lomanager2)\n\n"
            "Version {}\n\n"
            "Installation, update and removal of LibreOffice "
            "components in PCLinuxOS\n\n"
            "Copyright (C) 2023 programB\n\nThis program is licensed  "
            "under the terms of the GNU GPL version 3.\n"
        ).format(__version__)
        QMessageBox.about(self._app_main_view, _("About lomanager2"), about_text)

    def _install_from_local_copy(self):
        text = _(
            "Please chose the directory with saved packages.\n"
            "This procedure will check if those packages can be installed and "
            "if so it will install them but first it will remove any already "
            "installed Office, together with all its language packages."
        )
        self._local_copy_view.info_box.setText(text)
        # Set some dir before user makes proper choice
        self._local_copy_view.set_initial_dir("/home")

        # Open confirmation dialog before proceeding with installation
        if self._local_copy_view.exec():
            log.debug(_("Ok clicked: Installing from local copy..."))

            # Get the directory path provided by the user
            selected_dir = self._local_copy_view.selected_dir
            log.debug(_("The user selected: {}").format(selected_dir))

            # Create a separate thread worker that will run
            # selected procedure from the applogic,
            # pass any variables required by this procedure as well.
            self.procedure_thread = ProcedureWorker(
                function_to_run=self._app_logic.install_from_local_copy,
                local_copy_dir=selected_dir,
                progress_description=self.progress_description_signal.emit,
                progress_percentage=self.progress_signal.emit,
                overall_progress_description=self.overall_progress_description_signal.emit,
                overall_progress_percentage=self.overall_progress_signal.emit,
            )
            # Number of steps differs depending on procedure
            proc_steps = self._app_logic.local_copy_procedure_step_count
            self._progress_view.overall_progress_bar.setRange(0, proc_steps)
            # Window title differes depending on procedure
            self._progress_view.setWindowTitle(_("Applying changes"))
            # Show progress bar (check_system_state is not showing it)
            self._progress_view.progress_bar.setVisible(True)
            # Lock GUI elements, open progress window and start thread
            self.thread_worker_ready_signal.emit()
        else:
            log.debug(_("Cancel clicked: User gave up installing from local copy"))

    def _apply_changes(self):
        # Set keep_packages and force_java_download to NOT Checked
        # No assumptions should be made here, user has to explicitly demand
        # both package retention and download
        self._apply_changes_view.checkbox_keep_packages.setCheckState(
            Qt.CheckState.Unchecked
        )
        self._apply_changes_view.checkbox_force_java_download.setCheckState(
            Qt.CheckState.Unchecked
        )

        install_list, removal_list = self._app_logic.get_planned_changes()

        summary = ""
        if install_list:
            summary += _("Following components will be downloaded & installed:\n")
            for p in install_list:
                summary += "- " + p + "\n"
        summary += "\n"
        if removal_list:
            summary += _("Following components will be removed:\n")
            for p in removal_list:
                summary += "- " + p + "\n"
        if not install_list and not removal_list:
            summary = _("No changes to make")
        self._apply_changes_view.info_box.setText(summary)

        is_ok_to_apply_changes = True if install_list or removal_list else False
        is_ok_to_keep_packages = True if install_list else False
        self._apply_changes_view.apply_button.setEnabled(is_ok_to_apply_changes)
        self._apply_changes_view.checkbox_keep_packages.setEnabled(
            is_ok_to_keep_packages
        )
        # (force_java_download checkbox enable state is auto-decided in GUI)

        # Open a dialog and ask the user:
        # - whether to delete downloaded packages after installation
        # - if the java should be downloaded (despite it being installed)
        if self._apply_changes_view.exec():
            log.debug(_("Ok clicked. Applying changes..."))

            is_keep_packages_checked = (
                self._apply_changes_view.checkbox_keep_packages.isChecked()
            )
            is_force_java_download_checked = (
                self._apply_changes_view.checkbox_force_java_download.isChecked()
            )
            summary = summary.replace("\n", " ")
            summary += (
                _("Following components will be downloaded: - Java  ")
                if is_force_java_download_checked
                else " "
            )
            summary += (
                _("Packages will be kept for later use")
                if is_keep_packages_checked
                else _("Packages will not be kept for later use")
            )
            log.info(summary)

            # Create a separate thread worker that will run
            # selected procedure from the applogic,
            # pass any variables required by this procedure as well.
            self.procedure_thread = ProcedureWorker(
                function_to_run=self._app_logic.apply_changes,
                keep_packages=is_keep_packages_checked,
                force_java_download=is_force_java_download_checked,
                progress_description=self.progress_description_signal.emit,
                progress_percentage=self.progress_signal.emit,
                overall_progress_description=self.overall_progress_description_signal.emit,
                overall_progress_percentage=self.overall_progress_signal.emit,
            )
            # Number of steps differs depending on procedure
            proc_steps = self._app_logic.normal_procedure_step_count
            self._progress_view.overall_progress_bar.setRange(0, proc_steps)
            # Window title differes depending on procedure
            self._progress_view.setWindowTitle(_("Applying changes"))
            # Show progress bar (check_system_state is not showing it)
            self._progress_view.progress_bar.setVisible(True)
            # Lock GUI elements, open progress window and start thread
            self.thread_worker_ready_signal.emit()
        else:
            log.debug(_("Cancel clicked: User decided not to apply changes."))

    def _thread_start(self):
        """Make changes to the GUI and start a prepared worker in a new thread

        Thread workers are created by the following methods:
        _check_system_state
        _apply_changes
        _install_from_local_copy
        """

        # Block some GUI elements while the procedure is running
        self.is_GUI_locked_signal.emit(True)

        # Connect thread signals
        self.progress_description_signal.connect(self._update_progress_description)
        self.progress_signal.connect(self._update_progress)
        self.overall_progress_description_signal.connect(
            self._update_overall_progress_description
        )
        self.overall_progress_signal.connect(self._update_overall_progress)
        # WARNING: Just for tests. This MUST NOT be available to the user
        # self._progress_view.button_terminate.clicked.connect(
        #     self.procedure_thread.terminate
        # )
        self.procedure_thread.finished.connect(self._thread_stopped_or_terminated)

        # Open progress view
        self._progress_view.progress_description.setText("")
        self._progress_view.progress_bar.setValue(0)
        self._progress_view.overall_progress_description.setText("")
        self._progress_view.overall_progress_bar.setValue(0)
        self._progress_view.show()

        # Change cursor to indicate program is busy
        self._app_main_view.setCursor(Qt.CursorShape.WaitCursor)

        # Inform model that underlying data source will invalidate current data
        # (corresponding endResetModel is in the _rebuild_tree)
        self._software_menu_model.beginResetModel()

        # Start thread
        self.procedure_thread.start()

    def _update_progress_description(self, text: str):
        self._progress_view.progress_description.setText(text)

    def _update_progress(self, percentage: int):
        self._progress_view.progress_bar.setValue(percentage)

    def _update_overall_progress_description(self, text: str):
        self._progress_view.overall_progress_description.setText(text)

    def _update_overall_progress(self, percentage: int):
        self._progress_view.overall_progress_bar.setValue(percentage)

    def _thread_stopped_or_terminated(self):
        log.debug(_("Thread finished signal received."))

        self._progress_view.hide()
        self._app_main_view.unsetCursor()

        log.debug(_("Emitting rebuild_tree_signal"))
        self.rebuild_tree_signal.emit()

        log.debug(_("Emitting GUI locks signal to unlock GUI elements"))
        self.is_GUI_locked_signal.emit(False)

    def _warnings_show(self, warnings):
        error_icon = QMessageBox.Icon.Critical
        good_icon = QMessageBox.Icon.Information
        warnings_icon = QMessageBox.Icon.Warning

        if len(warnings) == 1:
            isOK, msg, expl = warnings[0]
            icon = good_icon if isOK else error_icon
            title = _("Success") if isOK else _("Problem")
        else:
            msg = ""
            expl = ""
            for i, warning in enumerate(warnings):
                msg += str(i + 1) + ") " + warning[1] + "\n\n"
                expl += str(i + 1) + ") " + warning[2] + "\n\n"
            icon = warnings_icon
            title = _("Warning")
        self._info_view.setWindowTitle(title)
        self._info_view.setText(msg)
        self._info_view.setDetailedText(expl)
        self._info_view.setIcon(icon)
        self._info_view.show()

    def _GUI_locks(self, is_locked: bool):
        # Apply master lock first
        for action in self._app_main_view.actions_list:
            action.setEnabled(not is_locked)
        self._office_view.setEnabled(not is_locked)
        self._clipart_view.setEnabled(not is_locked)
        self._langs_view.setEnabled(not is_locked)

        # Some elements need to be locked for other reasons
        if is_locked is False:
            self._app_main_view.actionInstallFromLocalCopy.setEnabled(
                not self._app_logic.global_flags.block_local_copy_install
            )

    def _check_system_state(self):
        log.debug(_("check system state signal emitted"))
        self.procedure_thread = ProcedureWorker(
            function_to_run=self._app_logic.check_system_state,
            progress_description=self.progress_description_signal.emit,
            progress_percentage=self.progress_signal.emit,
            overall_progress_description=self.overall_progress_description_signal.emit,
            overall_progress_percentage=self.overall_progress_signal.emit,
        )
        # Number of steps differs depending on procedure
        proc_steps = self._app_logic.check_system_procedure_step_count
        self._progress_view.overall_progress_bar.setRange(0, proc_steps)
        # Window title differes depending on procedure
        self._progress_view.setWindowTitle(_("Checking system state"))
        self._progress_view.progress_bar.setVisible(False)
        # Lock GUI elements, open progress window and start thread
        self.thread_worker_ready_signal.emit()

    def _cleanup_and_exit(self):
        log.debug(_("Quit clicked: User decided to finish using the app"))
        removed = self._app_logic.remove_temporary_dirs()
        if removed:
            log.info(_("Bye"))
        else:
            self.warnings_awaiting_signal.emit(self._app_logic.get_warnings())
        self._app_main_view.close()


class SignalWatchdog(QAbstractSocket):
    def __init__(self):
        """Propagates system signals from Python to QEventLoop"""
        # https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
        super().__init__(QAbstractSocket.SctpSocket, None)
        self.writer, self.reader = socket.socketpair()
        self.writer.setblocking(False)
        signal.set_wakeup_fd(self.writer.fileno())  # Python hook
        self.setSocketDescriptor(self.reader.fileno())  # Qt hook
        self.readyRead.connect(lambda: None)  # Dummy function call


def main(skip_update_check: bool = False):
    lomanager2App = QApplication([])

    # Makes the app quit on ctrl+c from console
    watchdog = SignalWatchdog()  # keeping the reference is needed
    signal.signal(signal.SIGINT, lambda sig, _: lomanager2App.quit())

    # Business logic
    app_logic = MainLogic(skip_update_check)

    # View
    main_window = AppMainWindow()

    # Adapter
    adapter = Adapter(app_logic=app_logic, main_view=main_window)

    # Make sure to check system state before anything else
    adapter._GUI_locks(is_locked=True)
    main_window.show()
    adapter.check_system_state_signal.emit()

    sys.exit(lomanager2App.exec_())  # exec_() for PySide2 compatibility


if __name__ == "__main__":
    main()
