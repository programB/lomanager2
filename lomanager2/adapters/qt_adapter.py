import sys

from pysidecompat import (
    QApplication,  # pyright: ignore
    QMessageBox,  # pyright: ignore
    QObject,  # pyright: ignore
    Signal,  # pyright: ignore
    Qt,  # pyright: ignore
)

from applogic.packagelogic import MainLogic
from gui import AppMainWindow
from viewmodels import (
    SoftwareMenuModel,
    SoftwareMenuRenderModel,
    LanguageMenuRenderModel,
)
from threads import ProcedureWorker
import configuration
from configuration import logging as log

checked = Qt.CheckState.Checked
unchecked = Qt.CheckState.Unchecked

columns = [
    {
        "name": "Program name",
        "show_in_main": True,
        "show_in_langs": False,
    },
    {
        "name": "language code",
        "show_in_main": True,
        "show_in_langs": True,
    },
    {
        "name": "language name",
        "show_in_main": False,
        "show_in_langs": True,
    },
    {
        "name": "version",
        "show_in_main": True,
        "show_in_langs": False,
    },
    {
        "name": "marked for removal?",
        "show_in_main": True,
        "show_in_langs": False,
    },
    {
        "name": "marked for install?",
        "show_in_main": True,
        "show_in_langs": True,
    },
    {
        "name": "installed?",
        "show_in_main": True,
        "show_in_langs": False,
    },
    {
        "name": "marked for download?",
        "show_in_main": True,
        "show_in_langs": False,
    },
]


class Adapter(QObject):
    # Register custom signals
    progress_description_signal = Signal(str)
    progress_signal = Signal(int)
    overall_progress_description_signal = Signal(str)
    overall_progress_signal = Signal(int)
    refresh_signal = Signal()
    thread_worker_ready_signal = Signal()
    warnings_awaiting_signal = Signal(list)
    check_system_state_signal = Signal()
    lock_unlock_GUI_signal = Signal()

    def __init__(self, app_logic, main_view) -> None:
        super().__init__()

        # Application's business logic
        self._app_logic = app_logic

        # Model (interprets data from app logic to be digestible by views)
        self._software_menu_model = SoftwareMenuModel(
            self._app_logic,
            column_names=[column.get("name") for column in columns],
        )

        # Views
        self._app_main_view = main_view
        self._software_view = self._app_main_view.software_view
        self._extra_langs_view = self._app_main_view.extra_langs_window.langs_view
        self._progress_view = self._app_main_view.progress_dialog
        self._info_view = self._app_main_view.info_dialog
        self._apply_changes_view = self._app_main_view.confirm_apply_dialog
        self._local_copy_view = self._app_main_view.confirm_local_copy_dialog

        # Render models (further filter/condition data before sending to views)
        self._software_menu_rendermodel = SoftwareMenuRenderModel(
            model=self._software_menu_model, parent=self._software_view
        )
        self._language_menu_rendermodel = LanguageMenuRenderModel(
            model=self._software_menu_model, parent=self._extra_langs_view
        )

        # Extra variables that can be set by the user in GUI
        # Initialize local _keep_packages variable from configuration
        self._keep_packages = configuration.keep_packages
        self._force_java_download = False
        self._local_copy_folder = None

        self._bind_views_to_models()
        self._connect_signals_and_slots()
        self._preset_views()

        # Flags blocking parts of the interface during certain operations
        self._is_packages_selecting_allowed = True
        self._is_starting_procedures_allowed = True

    def _bind_views_to_models(self):
        self._software_view.setModel(self._software_menu_rendermodel)
        self._extra_langs_view.setModel(self._language_menu_rendermodel)

    def _connect_signals_and_slots(self):
        # Option: Select additional language packs
        self._app_main_view.button_add_langs.clicked.connect(self._add_langs)

        # Option: Apply changes
        self._app_main_view.button_apply_changes.clicked.connect(self._apply_changes)

        # Option: Local copy install
        self._app_main_view.button_install_from_local_copy.clicked.connect(
            self._install_from_local_copy
        )

        # Option: Quit the app
        # TODO: Some cleanup procedures should be called here first
        #       like eg. closing the log file.
        #       ...and these should not be done here directly
        #       but through _app_logic
        self._app_main_view.button_quit.clicked.connect(self._app_main_view.close)

        # Internal Signal: Refresh state of the menu
        # TODO: test connect "refresh" (custom signal)
        self.refresh_signal.connect(self._refresh)

        # Internal Signal: Locks/Unlocks GUI elements
        self.lock_unlock_GUI_signal.connect(self._lock_unlock_GUI)

        # Internal Signal: starts already prepared thread
        self.thread_worker_ready_signal.connect(self._thread_start)

        # Internal Signal: Shows dialog with initial system state
        self.warnings_awaiting_signal.connect(self._warnings_show)

        # Internal Signal: Shows dialog with initial system state
        self.check_system_state_signal.connect(self._check_system_state)

    def _preset_views(self):
        for n, column in enumerate(columns):
            if column.get("show_in_main") is False:
                self._software_view.hideColumn(n)
            if column.get("show_in_langs") is False:
                self._extra_langs_view.hideColumn(n)
        self._extra_langs_view.setSortingEnabled(True)

    def _refresh(self):
        log.debug("Refreshing!")
        # Refresh package tree
        self._app_logic.refresh_state()
        # Inform model that underlying data source has finished changing
        self._software_menu_model.endResetModel()
        # and make it refresh itself
        self._software_menu_model.layoutChanged.emit()
        # Check if there are any messages that should
        # be shown to the user
        if self._app_logic.warnings:
            self.warnings_awaiting_signal.emit(self._app_logic.get_warnings())

    def _add_langs(self):
        self._app_main_view.extra_langs_window.exec()

    def _install_from_local_copy(self):
        text = (
            "Following procedure will inspect the chosen directory to find "
            + "out if LibreOffice can be installed using packages therein.\n"
            + "Please note that if check is successful any "
            + "already installed Office will be removed with all its "
            + "language packages."
        )
        self._local_copy_view.info_box.setText(text)
        self._local_copy_view.info_box.setWordWrap(True)
        # Ask the user for directory with saved packages
        if self._local_copy_view.exec():  # opens a dialog
            log.debug("Ok clicked: Installing from local copy...")

            # Get the directory path set by the user
            selected_dir = self._local_copy_view.selected_dir

            # Create separate thread worker passing
            # MainLogic's method to execute along with needed variables
            self.procedure_thread = ProcedureWorker(
                function_to_run=self._app_logic.install_from_local_copy,
                local_copy_folder=selected_dir,
                progress_description=self.progress_description_signal.emit,
                progress_percentage=self.progress_signal.emit,
                overall_progress_description=self.overall_progress_description_signal.emit,
                overall_progress_percentage=self.overall_progress_signal.emit,
            )
            # Lock GUI elements, open progress window and start thread
            self.thread_worker_ready_signal.emit()
        else:
            log.debug("Cancel clicked: User gave up installing from local copy")

    def _apply_changes(self):
        # Set initial state of keep_packages checkbox
        # (can be set in configuration)
        if self._keep_packages is True:
            self._apply_changes_view.checkbox_keep_packages.setCheckState(
                Qt.CheckState.Checked
            )
        else:
            self._apply_changes_view.checkbox_keep_packages.setCheckState(
                Qt.CheckState.Unchecked
            )

        # Set the initial state of the force_java_download checkbox
        # before displaying the dialog window
        fjd_state = checked if self._force_java_download else unchecked
        self._apply_changes_view.checkbox_force_java_download.setCheckState(fjd_state)
        to_install, to_remove = self._app_logic.get_planned_changes()
        if to_install or to_remove:
            text = ""
            if to_install:
                text += "Following components will be installed:\n"
                for p in to_install:
                    text += "- " + p + "\n"
            text += "\n"
            if to_remove:
                text += "Following components will be removed:\n"
                for p in to_remove:
                    text += "- " + p + "\n"
            self._apply_changes_view.info_box.setText(text)
            self._apply_changes_view.apply_button.setEnabled(True)
        else:
            text = "No changes to apply"
            self._apply_changes_view.info_box.setText(text)
            self._apply_changes_view.apply_button.setEnabled(False)

        # Open a dialog and ask the user:
        # - whether to delete downloaded packages after installation
        # - if the java should be downloaded (despite it being installed)
        if self._apply_changes_view.exec():
            log.debug("Ok clicked. Applying changes...")

            self._keep_packages = (
                self._apply_changes_view.checkbox_keep_packages.isChecked()
            )
            self._force_java_download = (
                self._apply_changes_view.checkbox_force_java_download.isChecked()
            )

            # Create separate thread worker passing
            # MainLogic's method to execute along with needed variables
            self.procedure_thread = ProcedureWorker(
                function_to_run=self._app_logic.apply_changes,
                keep_packages=self._keep_packages,
                force_java_download=self._force_java_download,
                progress_description=self.progress_description_signal.emit,
                progress_percentage=self.progress_signal.emit,
                overall_progress_description=self.overall_progress_description_signal.emit,
                overall_progress_percentage=self.overall_progress_signal.emit,
            )
            # Lock GUI elements, open progress window and start thread
            self.thread_worker_ready_signal.emit()
        else:
            log.debug("Cancel clicked: User decided not to apply changes.")

    def _thread_start(self):
        # Block some GUI elements while the procedure is running
        self._is_packages_selecting_allowed = False
        self._is_starting_procedures_allowed = False
        self.lock_unlock_GUI_signal.emit()

        # Connect thread signals
        self.progress_description_signal.connect(self._update_progress_description)
        self.progress_signal.connect(self._update_progress)
        self.overall_progress_description_signal.connect(
            self._update_overall_progress_description
        )
        self.overall_progress_signal.connect(self._update_overall_progress)
        # TODO: Just for test. This MUST not be available to user.
        self._progress_view.button_terminate.clicked.connect(
            self.procedure_thread.terminate
        )
        self.procedure_thread.finished.connect(self._thread_stopped_or_terminated)

        # Open progress view
        self._progress_view.progress_description.setText("")
        self._progress_view.progress_bar.setValue(0)
        self._progress_view.overall_progress_description.setText("")
        self._progress_view.overall_progress_bar.setValue(0)
        self._progress_view.overall_progress_bar.setTextVisible(False)
        self._progress_view.show()

        # Change cursor
        self._app_main_view.setCursor(Qt.WaitCursor)

        # Let the model know the data it currently has
        # will become invalid
        self._software_menu_model.beginResetModel()

        # Start self._procedure_thread created in either
        # _confirm_and_start_applying_changes
        # or _choose_dir_and_install_from_local_copy
        # or _run_flags_logic
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
        log.debug("Thread finished signal received.")
        self._app_main_view.unsetCursor()
        self._progress_view.hide()
        log.debug("Emiting refresh signal to rebuild packages state")
        self.refresh_signal.emit()
        log.debug("Emiting GUI locks signal to unlock GUI elements")
        self._is_packages_selecting_allowed = True
        self._is_starting_procedures_allowed = True
        self.lock_unlock_GUI_signal.emit()

    def _warnings_show(self, warnings):
        error_icon = QMessageBox.Icon.Critical
        good_icon = QMessageBox.Icon.Information
        warnings_icon = QMessageBox.Icon.Warning

        if len(warnings) == 1:
            isOK, msg = warnings[0]
            icon = good_icon if isOK else error_icon
            title = "Success" if isOK else "Problem"
        else:
            msg = ""
            for i, warning in enumerate(warnings):
                msg += str(i + 1) + ") " + warning[1] + "\n\n"
            icon = warnings_icon
            title = "Warning"
        self._info_view.setWindowTitle(title)
        self._info_view.setText(msg)
        self._info_view.setIcon(icon)
        self._info_view.show()

    def _lock_unlock_GUI(self):
        if self._is_packages_selecting_allowed is True:
            self._software_view.setEnabled(True)
        else:
            self._software_view.setEnabled(False)

        if (
            self._is_starting_procedures_allowed
            and not self._app_logic.global_flags.block_normal_procedure
        ):
            is_apply_enabled = True
        else:
            is_apply_enabled = False
        self._app_main_view.button_apply_changes.setEnabled(is_apply_enabled)

        if (
            self._is_starting_procedures_allowed
            and not self._app_logic.global_flags.block_local_copy_install
        ):
            is_local_enabled = True
        else:
            is_local_enabled = False
        self._app_main_view.button_install_from_local_copy.setEnabled(is_local_enabled)

    def _check_system_state(self):
        print("check system state signal emitted")
        self.procedure_thread = ProcedureWorker(
            function_to_run=self._app_logic.flags_logic,
            progress_description=self.progress_description_signal.emit,
            progress_percentage=self.progress_signal.emit,
            overall_progress_description=self.overall_progress_description_signal.emit,
            overall_progress_percentage=self.overall_progress_signal.emit,
        )
        # Lock GUI elements, open progress window and start thread
        self.thread_worker_ready_signal.emit()


def main():
    lomanager2App = QApplication([])

    # Business logic
    app_logic = MainLogic()

    # View
    main_window = AppMainWindow()

    # Adapter
    adapter = Adapter(app_logic=app_logic, main_view=main_window)
    adapter._lock_unlock_GUI()

    main_window.show()
    adapter.check_system_state_signal.emit()
    sys.exit(lomanager2App.exec_())  # exec_() for PySide2 compatibility


if __name__ == "__main__":
    main()
