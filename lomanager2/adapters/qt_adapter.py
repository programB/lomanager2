import sys

from PySide6.QtWidgets import (
    QApplication,
)
from PySide6.QtCore import (
    QObject,
    Signal,
    Qt,
)

from applogic.packagelogic import MainLogic
from gui import AppMainWindow
from viewmodels import PackageMenuViewModel
from threads import InstallProcedureWorker
import configuration


class Adapter(QObject):
    # Register custom signals
    refresh_signal = Signal()
    status_signal = Signal(dict)

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
        self._keep_packages = False
        self._local_copy_folder = None

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

        # Internal Signal: Keep packages checkbox
        self._main_view.confirm_apply_view.checkbox_keep_packages.stateChanged.connect(
            self._set_keep_packages_state
        )

    def _refresh_package_menu_state(self):
        configuration.logging.debug("Refreshing!")
        self._main_model.refresh_state()

    def _choose_dir_and_install_from_local_copy(self):
        # Ask the user to point to a directory with saved packages
        # intended for installation (opens a dialog).
        if self._main_view.confirm_local_copy_view.exec():
            configuration.logging.debug("Installing from local copy...")
            # TODO: Implement getting the folder path,
            #       creating worker thread and starting it
        else:
            configuration.logging.debug(
                "Cancel clicked: User gave up installing from local copy"
            )

    def _confirm_and_start_applying_changes(self, install_mode: str):
        # Ask the user for confirmation
        if self._main_view.confirm_apply_view.exec():
            configuration.logging.debug("Applying changes...")
            # Create separate thread worker
            # and pass the MainLogic's method to execute
            # along with values (collected from GUI) it would need.
            self.apply_changes_thread = InstallProcedureWorker(
                function_to_run=self._main_model.apply_changes,
                keep_packages=self._keep_packages,
                install_mode=install_mode,
                local_copy_folder=self._local_copy_folder,
                report_status=self.status_signal.emit,
            )
            # Connect thread signals
            self.apply_changes_thread.progress.connect(self._progress_was_made)
            self.apply_changes_thread.finished.connect(
                self._thread_stopped_or_terminated
            )
            # TODO: Just for test. This MUST not be available to user.
            self._progress_view.button_terminate.clicked.connect(
                self.apply_changes_thread.terminate
            )

            self._progress_view.show()
            # TODO: Block certain buttons in the main interface here to
            #       prevent from another thread being started. But not
            #       all of them (eg. log output (aka console)
            #       should be operational)

            self.apply_changes_thread.start()  # start the prepared thread
        else:
            configuration.logging.debug(
                "Cancel clicked: User decided not to apply changes."
            )

    def _progress_was_made(self, progress):
        configuration.logging.debug(
            f"Current progress (received in adapter's slot): {progress}"
        )
        self._progress_view.progress_bar.setValue(progress)

    def _thread_stopped_or_terminated(self):
        self._progress_view.hide()
        self._progress_view.progress_bar.setValue(0)
        configuration.logging.debug("Thread finished signal received.")
        configuration.logging.debug(
            f"thread: {self.apply_changes_thread}\n"
            f"is running?: {self.apply_changes_thread.isRunning()}\n"
            f"is finished?: {self.apply_changes_thread.isFinished()}"
        )
        configuration.logging.debug("Emiting refresh signal to rebuild packages state")
        self.refresh_signal.emit()

    def _set_keep_packages_state(self):
        state = self._main_view.confirm_apply_view.checkbox_keep_packages.checkState()
        configuration.logging.debug(f"in GUI keep_packages checkbox is set to: {state}")
        # Qt.PartiallyChecked doesn't make sense in this application
        if state == Qt.CheckState.Checked:
            self._keep_packages = True
        if state == Qt.CheckState.Unchecked:
            self._keep_packages = False

    def _display_status_information(self, status):
        info = ""
        if "explanation" in status.keys():
            info = status["explanation"]
        self._main_view.info_dialog.setText(info)
        self._main_view.open_information_modal_window()


def main():
    lomanager2App = QApplication([])

    # Model
    app_logic = MainLogic()

    # View
    main_window = AppMainWindow()

    # Adapter
    adapter = Adapter(app_main_model=app_logic, app_main_view=main_window)

    main_window.show()
    sys.exit(lomanager2App.exec())


if __name__ == "__main__":
    main()
