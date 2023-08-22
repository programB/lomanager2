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
    PackageMenuViewModel,
    MainPackageMenuRenderModel,
    LanguageMenuRenderModel,
)
from threads import ProcedureWorker
import configuration
from configuration import logging as log

checked = Qt.CheckState.Checked
unchecked = Qt.CheckState.Unchecked


class Adapter(QObject):
    # Register custom signals
    progress_description_signal = Signal(str)
    progress_signal = Signal(int)
    overall_progress_description_signal = Signal(str)
    overall_progress_signal = Signal(int)
    refresh_signal = Signal()
    worker_ready_signal = Signal()
    warning_signal = Signal(list)
    init_signal = Signal()
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
        self.column_names = [
            "Program name",
            "virtual package type",
            "language name",
            "version",
            "marked for removal?",
            "marked for install?",
            "is installed?",
            "is marked for download?",
        ]
        self._package_menu_viewmodel = PackageMenuViewModel(
            self._main_model, self.column_names
        )
        self._package_menu_rendermodel = MainPackageMenuRenderModel(
            self._package_menu_view
        )
        # TODO: Does not exist yet - Implement
        # extra_langs_menu_viewmodel = LangsMenuViewModel()
        self._language_menu_rendermodel = LanguageMenuRenderModel(
            self._extra_langs_view
        )

        # Extra variables that can be set by the user in GUI
        # Initialize local _keep_packages variable from configuration
        self._keep_packages = configuration.keep_packages
        self._force_java_download = False
        self._local_copy_folder = None

        self._bind_views_to_viewmodels()
        self._connect_signals_and_slots()

        # Flags blocking parts of the interface during certain operations
        self._is_packages_selecting_allowed = True
        self._is_starting_procedures_allowed = True

    def _bind_views_to_viewmodels(self):
        # self._package_menu_view.setModel(self._package_menu_viewmodel)
        self._package_menu_rendermodel.setSourceModel(self._package_menu_viewmodel)
        self._package_menu_view.setModel(self._package_menu_rendermodel)
        self._package_menu_view.hideColumn(self.column_names.index("language name"))
        # TODO: Implement - does not exist yet
        # self._extra_langs_view.setModel(self._langs_menu_viewmodel)
        self._language_menu_rendermodel.setSourceModel(self._package_menu_viewmodel)
        self._extra_langs_view.setModel(self._language_menu_rendermodel)

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

        # Internal Signal: Locks/Unlocks GUI elements
        self.GUI_locks_signal.connect(self.change_GUI_locks)

        # Internal Signal: starts already prepared thread
        self.worker_ready_signal.connect(self._start_procedure_thread)

        # Internal Signal: Shows dialog with initial system state
        self.warning_signal.connect(self._show_warnings)

        # Internal Signal: Shows dialog with initial system state
        self.init_signal.connect(self._run_flags_logic)

    def _refresh_package_menu_state(self):
        log.debug("Refreshing!")
        self._main_model.refresh_state()
        self._package_menu_viewmodel.layoutChanged.emit()
        # Check if there are any messages that should
        # be shown to the user
        if self._main_model.warnings:
            self.warning_signal.emit(self._main_model.get_warnings())

    def _choose_dir_and_install_from_local_copy(self):
        text = (
            "Following procedure will inspect the chosen directory to find "
            + "out if LibreOffice can be installed using packages therein.\n"
            + "Please note that if check is successful any "
            + "already installed Office will be removed with all its "
            + "language packages."
        )
        self._main_view.confirm_local_copy_view.info_box.setText(text)
        self._main_view.confirm_local_copy_view.info_box.setWordWrap(True)
        # Ask the user for directory with saved packages
        if self._main_view.confirm_local_copy_view.exec():  # opens a dialog
            log.debug("Ok clicked: Installing from local copy...")

            # Get the directory path set by the user
            selected_dir = self._main_view.confirm_local_copy_view.selected_dir

            # Create separate thread worker passing
            # MainLogic's method to execute along with needed variables
            self.procedure_thread = ProcedureWorker(
                function_to_run=self._main_model.install_from_local_copy,
                local_copy_folder=selected_dir,
                progress_description=self.progress_description_signal.emit,
                progress_percentage=self.progress_signal.emit,
                overall_progress_description=self.overall_progress_description_signal.emit,
                overall_progress_percentage=self.overall_progress_signal.emit,
            )
            # Lock GUI elements, open progress window and start thread
            self.worker_ready_signal.emit()
        else:
            log.debug("Cancel clicked: User gave up installing from local copy")

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

        # Set the initial state of the force_java_download checkbox
        # before displaying the dialog window
        fjd_state = checked if self._force_java_download else unchecked
        self._main_view.confirm_apply_view.checkbox_force_java_download.setCheckState(
            fjd_state
        )
        to_install, to_remove = self._main_model.get_planned_changes()
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
            self._main_view.confirm_apply_view.info_box.setText(text)
            self._main_view.confirm_apply_view.apply_button.setEnabled(True)
        else:
            text = "No changes to apply"
            self._main_view.confirm_apply_view.info_box.setText(text)
            self._main_view.confirm_apply_view.apply_button.setEnabled(False)

        # Open a dialog and ask the user:
        # - whether to delete downloaded packages after installation
        # - if the java should be downloaded (despite it being installed)
        if self._main_view.confirm_apply_view.exec():
            log.debug("Ok clicked. Applying changes...")

            self._keep_packages = (
                self._main_view.confirm_apply_view.checkbox_keep_packages.isChecked()
            )
            self._force_java_download = (
                self._main_view.confirm_apply_view.checkbox_force_java_download.isChecked()
            )

            # Create separate thread worker passing
            # MainLogic's method to execute along with needed variables
            self.procedure_thread = ProcedureWorker(
                function_to_run=self._main_model.apply_changes,
                keep_packages=self._keep_packages,
                force_java_download=self._force_java_download,
                progress_description=self.progress_description_signal.emit,
                progress_percentage=self.progress_signal.emit,
                overall_progress_description=self.overall_progress_description_signal.emit,
                overall_progress_percentage=self.overall_progress_signal.emit,
            )
            # Lock GUI elements, open progress window and start thread
            self.worker_ready_signal.emit()
        else:
            log.debug("Cancel clicked: User decided not to apply changes.")

    def _start_procedure_thread(self):
        # Block some GUI elements while the procedure is running
        self._is_packages_selecting_allowed = False
        self._is_starting_procedures_allowed = False
        self.GUI_locks_signal.emit()

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
        self._main_view.setCursor(Qt.WaitCursor)

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
        self._main_view.unsetCursor()
        self._progress_view.hide()
        log.debug("Emiting refresh signal to rebuild packages state")
        self.refresh_signal.emit()
        log.debug("Emiting GUI locks signal to unlock GUI elements")
        self._is_packages_selecting_allowed = True
        self._is_starting_procedures_allowed = True
        self.GUI_locks_signal.emit()

    def _show_warnings(self, warnings):
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
        self._main_view.info_dialog.setWindowTitle(title)
        self._main_view.info_dialog.setText(msg)
        self._main_view.info_dialog.setIcon(icon)
        self._main_view.info_dialog.show()

    def change_GUI_locks(self):
        if self._is_packages_selecting_allowed is True:
            self._main_view.package_menu_view.setEnabled(True)
        else:
            self._main_view.package_menu_view.setEnabled(False)

        if (
            self._is_starting_procedures_allowed
            and not self._main_model.global_flags.block_normal_procedure
        ):
            is_apply_enabled = True
        else:
            is_apply_enabled = False
        self._main_view.button_apply_changes.setEnabled(is_apply_enabled)

        if (
            self._is_starting_procedures_allowed
            and not self._main_model.global_flags.block_local_copy_install
        ):
            is_local_enabled = True
        else:
            is_local_enabled = False
        self._main_view.button_install_from_local_copy.setEnabled(is_local_enabled)

    def _run_flags_logic(self):
        print("init signal emitted")
        self.procedure_thread = ProcedureWorker(
            function_to_run=self._main_model.flags_logic,
            progress_description=self.progress_description_signal.emit,
            progress_percentage=self.progress_signal.emit,
            overall_progress_description=self.overall_progress_description_signal.emit,
            overall_progress_percentage=self.overall_progress_signal.emit,
        )
        # Lock GUI elements, open progress window and start thread
        self.worker_ready_signal.emit()
        # self._main_model.flags_logic()


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
    adapter.init_signal.emit()
    sys.exit(lomanager2App.exec_())  # exec_() for PySide2 compatibility


if __name__ == "__main__":
    main()
