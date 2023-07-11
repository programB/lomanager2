import sys

from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
)
from PySide6.QtCore import (
    QObject,
    Signal,
    Qt,
)

from applogic.packagelogic import MainLogic
from gui import AppMainWindow
from viewmodels import PackageMenuViewModel
from threads import ProcedureWorker
import configuration


class Adapter(QObject):
    # Register custom signals
    progress = Signal(int)
    refresh_signal = Signal()
    status_signal = Signal(dict)
    worker_ready_signal = Signal()
    GUI_locks_signal = Signal()

    def __init__(self, app_main_model, app_main_view) -> None:
        super().__init__()

        # TODO:  Naming: too many different names for the same thing
        #        logic/model/package_menu etc

        # Models
        self._main_model = app_main_model

        # Views
        self._main_view = app_main_view
        self._package_menu_view = self._main_view.package_menu_view
        self._extra_langs_view = self._main_view.extra_langs_view.langs_view
        self._progress_view = self._main_view.progress_view

        # Viewmodels
        # The viewmodel (PackageMenuViewModel) for the object responsible
        # for dealing with packages selection _main_view
        # is instantiated here.
        # In turn MainLogic object (_main_model) is passed to
        # PackageMenuViewModel constructor to link PackageMenuViewModel
        # to the underlying application logic.
        # This is done here explicitly although PackageMenuViewModel
        # has to now the details of methods exposed by MainLogic
        self._package_menu_viewmodel = PackageMenuViewModel(self._main_model)
        # TODO: Does not exist yet - Implement
        # extra_langs_menu_viewmodel = LangsMenuViewModel()

        # Extra variables that can be set by the user in GUI
        # Initialize local _keep_packages variable from configuration
        self._keep_packages = configuration.keep_packages
        self._local_copy_folder = None

        # Flags blocking parts of the interface during certain operations
        self._is_packages_selecting_allowed = True
        self._is_starting_procedures_allowed = True

        self._bind_views_to_viewmodels()
        self._connect_signals_and_slots()

    def _bind_views_to_viewmodels(self):
        self._package_menu_view.setModel(self._package_menu_viewmodel)
        # TODO: Implement - does not exist yet
        # self._extra_langs_view.setModel(self._langs_menu_viewmodel)

    def _connect_signals_and_slots(self):
        # Option: Local copy installation
        self._main_view.button_install_from_local_copy.clicked.connect(
            self._choose_dir_and_install_from_local_copy
        )

        # Option: Select additional language packs
        self._main_view.button_add_langs.clicked.connect(
            self._main_view.open_langs_selection_modal_window
        )

        # Option: Apply changes
        # TODO: Should this button be disabled
        #       until the procedure is finished?
        self._main_view.button_apply_changes.clicked.connect(
            self._confirm_and_start_applying_changes
        )

        # Option: Quit the app
        # TODO: Some cleanup procedures should be called here first
        #       like eg. closing the log file.
        #       ...and these should not be called directly of course
        #       but _main_model should be providing that functions.
        self._main_view.button_quit.clicked.connect(self._main_view.close)

        # Internal Signal: Refresh state of the menu
        # TODO: test connect "refresh" (custom signal)
        self.refresh_signal.connect(self._refresh_package_menu_state)

        # Internal Signal: Shows dialog with information returned by procedures
        self.status_signal.connect(self._display_status_information)

        # Internal Signal: Locks/Unlocks GUI elements
        self.GUI_locks_signal.connect(self.change_GUI_locks)

        # Internal Signal: starts already prepared thread
        self.worker_ready_signal.connect(self._start_procedure_thread)

    def _refresh_package_menu_state(self):
        configuration.logging.debug("Refreshing!")
        self._main_model.refresh_state()

    def _choose_dir_and_install_from_local_copy(self):
        # Ask the user for directory with saved packages
        if self._main_view.confirm_local_copy_view.exec():  # opens a dialog
            configuration.logging.debug("Ok clicked: Installing from local copy...")

            # Get the directory path set by the user
            selected_dir = self._main_view.confirm_local_copy_view.selected_dir

            # Create separate thread worker passing
            # MainLogic's method to execute along with needed variables
            self.procedure_thread = ProcedureWorker(
                function_to_run=self._main_model.install_from_local_copy,
                local_copy_folder=selected_dir,
                report_status=self.status_signal.emit,
                inform_about_progress=self.progress.emit,
            )
            # Lock GUI elements, open progress window and start thread
            self.worker_ready_signal.emit()
        else:
            configuration.logging.debug(
                "Cancel clicked: User gave up installing from local copy"
            )

    def _confirm_and_start_applying_changes(self):
        # Set initial state of keep_packages checkbox
        # (can be set in configuration)
        if self._keep_packages is True:
            self._main_view.confirm_apply_view.checkbox_keep_packages.setCheckState(
                Qt.CheckState.Checked
            )
        else:
            self._main_view.confirm_apply_view.checkbox_keep_packages.setCheckState(
                Qt.CheckState.Unchecked
            )
        # Ask the user wheter to delete downloaded packages after installation
        if self._main_view.confirm_apply_view.exec():  # open a dialog
            configuration.logging.debug("Ok clicked. Applying changes...")

            # Get user decision
            self._keep_packages = (
                self._main_view.confirm_apply_view.checkbox_keep_packages.isChecked()
            )

            # Create separate thread worker passing
            # MainLogic's method to execute along with needed variables
            self.procedure_thread = ProcedureWorker(
                function_to_run=self._main_model.apply_changes,
                keep_packages=self._keep_packages,
                report_status=self.status_signal.emit,
                inform_about_progress=self.progress.emit,
            )
            # Lock GUI elements, open progress window and start thread
            self.worker_ready_signal.emit()
        else:
            configuration.logging.debug(
                "Cancel clicked: User decided not to apply changes."
            )

    def _start_procedure_thread(self):
        # Block some GUI elements while the procedure is running
        self._is_packages_selecting_allowed = False
        self._is_starting_procedures_allowed = False
        self.GUI_locks_signal.emit()

        # Connect thread signals
        self.progress.connect(self._progress_was_made)
        # TODO: Just for test. This MUST not be available to user.
        self._progress_view.button_terminate.clicked.connect(
            self.procedure_thread.terminate
        )
        self.procedure_thread.finished.connect(self._thread_stopped_or_terminated)

        # Open progress view
        self._progress_view.show()
        # Start self._procedure_thread created in either
        # _confirm_and_start_applying_changes
        # or _choose_dir_and_install_from_local_copy
        self.procedure_thread.start()

    def _progress_was_made(self, progress):
        configuration.logging.debug(
            f"Current progress (received in adapter's slot): {progress}"
        )
        self._progress_view.progress_bar.setValue(progress)

    def _thread_stopped_or_terminated(self):
        configuration.logging.debug("Thread finished signal received.")
        self._progress_view.hide()
        self._progress_view.progress_bar.setValue(0)
        configuration.logging.debug("Emiting refresh signal to rebuild packages state")
        self.refresh_signal.emit()
        configuration.logging.debug("Emiting GUI locks signal to unlock GUI elements")
        self._is_packages_selecting_allowed = True
        self._is_starting_procedures_allowed = True
        self.GUI_locks_signal.emit()

    def _display_status_information(self, status: dict):
        if "explanation" in status.keys() and "is_OK" in status.keys():
            info = status["explanation"]
            if status["is_OK"] is True:
                self._main_view.info_dialog.setWindowTitle("Success")
                self._main_view.info_dialog.setText(info)
                self._main_view.info_dialog.setIcon(QMessageBox.Icon.Information)
                self._main_view.info_dialog.exec()
            if status["is_OK"] is False:
                self._main_view.info_dialog.setWindowTitle("Problem")
                self._main_view.info_dialog.setText(info)
                self._main_view.info_dialog.setIcon(QMessageBox.Icon.Warning)
                self._main_view.info_dialog.exec()

    def change_GUI_locks(self):
        # TODO: Query MainLogic for allowed/disallowed operations
        #       and set controls in GUI accordingly
        if self._is_packages_selecting_allowed is True:
            self._main_view.package_menu_view.setEnabled(True)
        else:
            self._main_view.package_menu_view.setEnabled(False)

        if self._is_starting_procedures_allowed is True:
            self._main_view.button_apply_changes.setEnabled(True)
            self._main_view.button_install_from_local_copy.setEnabled(True)
            self._main_view.button_add_langs.setEnabled(True)
        else:
            self._main_view.button_apply_changes.setEnabled(False)
            self._main_view.button_install_from_local_copy.setEnabled(False)
            self._main_view.button_add_langs.setEnabled(False)


def main():
    lomanager2App = QApplication([])

    # Model
    app_logic = MainLogic()

    # View
    main_window = AppMainWindow()

    # Adapter
    adapter = Adapter(app_main_model=app_logic, app_main_view=main_window)
    adapter.change_GUI_locks()

    main_window.show()
    sys.exit(lomanager2App.exec())


if __name__ == "__main__":
    main()
