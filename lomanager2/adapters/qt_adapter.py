import sys

from pysidecompat import (
    QApplication,  # pyright: ignore
    QMessageBox,  # pyright: ignore
    QObject,  # pyright: ignore
    Signal,  # pyright: ignore
    Qt,  # pyright: ignore
    QItemDelegate,  # pyright: ignore
    QEvent,  # pyright: ignore
    QtGui,  # pyright: ignore
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

columns = {
    "Program name": {
        "id": 0,
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
    "language code": {
        "id": 1,
        "show_in_software_view": True,
        "show_in_langs_view": True,
    },
    "language name": {
        "id": 2,
        "show_in_software_view": False,
        "show_in_langs_view": True,
    },
    "version": {
        "id": 3,
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
    "marked for removal?": {
        "id": 4,
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
    "marked for install?": {
        "id": 5,
        "show_in_software_view": True,
        "show_in_langs_view": True,
    },
    "installed?": {
        "id": 6,
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
    "marked for download?": {
        "id": 7,
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
}


class PushButtonDelegate(QItemDelegate):
    def __init__(self, parent=None):
        super(PushButtonDelegate, self).__init__(parent)

    def editorEvent(self, event, model, option, index):
        is_remove_col = index.column() == columns.get("marked for removal?").get("id")
        is_install_col = index.column() == columns.get("marked for install?").get("id")
        if is_remove_col or is_install_col:
            is_visible = bool(index.model().data(index, Qt.ItemDataRole.UserRole + 2))
            if is_visible:
                markstate = index.model().data(index, Qt.ItemDataRole.DisplayRole)
                is_enabled = bool(
                    index.model().data(index, Qt.ItemDataRole.UserRole + 3)
                )
                if (
                    event.type() == QEvent.Type.MouseButtonRelease
                    and event.button() == Qt.MouseButton.LeftButton
                    and is_enabled
                ) or (
                    event.type() == QEvent.Type.KeyPress
                    and event.key() == Qt.Key.Key_Space
                    and is_enabled
                ):
                    print("DELEGATE: ≈≈≈≈≈≈≈ SETTING DATA BACK TO THE MODEL ≈≈≈≈≈≈≈")
                    print(f"switching markstate: {markstate} -> {not markstate}")
                    model.setData(index, str(not markstate), Qt.ItemDataRole.EditRole)
                    return True
                elif event.type() == QEvent.Type.MouseButtonDblClick:
                    print("2-clicked MOUSE")
                    # Capture DoubleClick here
                    # (accept event to prevent cell editor getting opened)
                    event.accept()
                    return True

                else:
                    # print(f"other editorEvent: {event}")
                    # Ignore other events
                    return True
            else:
                return True
        else:
            return False

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        is_remove_col = index.column() == columns.get("marked for removal?").get("id")
        is_install_col = index.column() == columns.get("marked for install?").get("id")
        if is_remove_col or is_install_col:
            is_visible = bool(index.model().data(index, Qt.ItemDataRole.UserRole + 2))
            if is_visible:
                # Do the button painting here
                painter.save()

                markstate = bool(index.model().data(index, Qt.ItemDataRole.EditRole))
                is_enabled = bool(
                    index.model().data(index, Qt.ItemDataRole.UserRole + 3)
                )

                normal_button_color = QtGui.QColor("green")
                normal_button_border_color = QtGui.QColor("dark green")
                normal_text_color = QtGui.QColor("white")

                disabled_button_color = QtGui.QColor("#635f5e")
                disabled_button_border_color = QtGui.QColor("#484544")
                disabled_text_color = QtGui.QColor("#b4adaa")

                # Ignore the check: if option.state & QStyle.State_Selected
                # and remove highlight around the button irrespective its
                # selection/focus state
                painter.eraseRect(option.rect)

                # controls border color (and text color)
                pen = painter.pen()
                pen.setColor(
                    normal_button_border_color
                    if is_enabled
                    else disabled_button_border_color
                )
                painter.setPen(pen)

                # controls the fill color
                painter.setBrush(
                    normal_button_color if is_enabled else disabled_button_color
                )

                # Draw the "button"
                delta = 2
                option.rect.adjust(delta, delta, -delta, -delta)
                x, y, w, h = option.rect.getRect()
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.drawRoundedRect(x, y, w, h, 10, 10)

                # change pen color to draw text
                pen.setColor(normal_text_color if is_enabled else disabled_text_color)
                painter.setPen(pen)
                button_text = "remove" if is_remove_col else "install"
                painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, button_text)

                # draw a checkbox
                x, y, w, h = option.rect.getRect()
                new_h = 0.6 * h
                new_w = new_h
                new_y = y + h / 2 - new_h / 2
                new_x = x + new_w
                option.rect.setRect(new_x, new_y, new_w, new_h)
                self.drawCheck(
                    painter,
                    option,
                    option.rect,
                    Qt.Checked if markstate else Qt.Unchecked,
                )
                painter.restore()
            else:
                # QItemDelegate.paint(self, painter, option, index)
                # Do not draw anything - leave the cell empty
                pass
        else:
            # Use default delegates to paint other cells
            QItemDelegate.paint(self, painter, option, index)


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
    lock_unlock_GUI_signal = Signal()

    def __init__(self, app_logic, main_view) -> None:
        super().__init__()

        # Application's business logic
        self._app_logic = app_logic

        # Model (transforms data from app logic to form digestible by views)
        self._software_menu_model = SoftwareMenuModel(
            self._app_logic,
            column_names=[column for column in columns],
        )

        # Views
        self._app_main_view = main_view
        self._software_view = self._app_main_view.software_view
        self._langs_view = self._app_main_view.extra_langs_window.langs_view
        self._progress_view = self._app_main_view.progress_dialog
        self._info_view = self._app_main_view.info_dialog
        self._apply_changes_view = self._app_main_view.confirm_apply_dialog
        self._local_copy_view = self._app_main_view.confirm_local_copy_dialog

        # Render models (further filter/condition data before sending to views)
        self._software_menu_rendermodel = SoftwareMenuRenderModel(
            model=self._software_menu_model, parent=self._software_view
        )
        self._language_menu_rendermodel = LanguageMenuRenderModel(
            model=self._software_menu_model, parent=self._langs_view
        )

        # Delegates
        # contructing delegate with main WINDOW as parent ensures it will
        # be propertly deleted
        self.check_button = PushButtonDelegate(parent=self._app_main_view)
        self._software_view.setItemDelegate(self.check_button)
        self._langs_view.setItemDelegate(self.check_button)

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
        self._langs_view.setModel(self._language_menu_rendermodel)

    def _connect_signals_and_slots(self):
        # Option available for the user: Select additional language packs
        self._app_main_view.button_add_langs.clicked.connect(self._add_langs)

        # Option available for the user: Apply selected changes
        self._app_main_view.button_apply_changes.clicked.connect(self._apply_changes)

        # Option available for the user: Install from local copy
        self._app_main_view.button_install_from_local_copy.clicked.connect(
            self._install_from_local_copy
        )

        # Option available for the user: Quit the app
        # TODO: Some cleanup procedures should be called here first
        #       like eg. closing the log file.
        #       ...and these should not be done here directly
        #       but through _app_logic
        self._app_main_view.button_quit.clicked.connect(self._app_main_view.close)

        # Internal signal: Ask applogic to redo package tree from scratch
        self.rebuild_tree_signal.connect(self._rebuild_tree)

        # Internal signal: Lock/Unlock GUI elements
        self.lock_unlock_GUI_signal.connect(self._lock_unlock_GUI)

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
                self._software_view.hideColumn(n)
            if column_flags.get("show_in_langs_view") is False:
                self._langs_view.hideColumn(n)
        self._langs_view.setSortingEnabled(True)

    def _rebuild_tree(self):
        log.debug("Starting package tree rebuild!")
        # Rebuild package tree
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

    def _install_from_local_copy(self):
        # Open confirmation dialog before proceeding with installation
        text = (
            "Following procedure will inspect the chosen directory to find "
            + "out if LibreOffice can be installed using packages therein.\n"
            + "Please note that if check is successful any "
            + "already installed Office will be removed with all its "
            + "language packages."
        )
        self._local_copy_view.info_box.setText(text)
        self._local_copy_view.info_box.setWordWrap(True)
        if self._local_copy_view.exec():
            log.debug("Ok clicked: Installing from local copy...")

            # Get the directory path provided by the user
            selected_dir = self._local_copy_view.selected_dir

            # Create a separate thread worker that will run
            # selected procedure from the applogic,
            # pass any variables required by this procedure as well.
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

            # Create a separate thread worker that will run
            # selected procedure from the applogic,
            # pass any variables required by this procedure as well.
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
        """Make changes to the GUI and start a prepared worker in a new thread

        Thread workers are created by the following methods:
        _check_system_state
        _apply_changes
        _install_from_local_copy
        """

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
        # TODO: Just for tests. This MUST NOT be available to the user
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

        # Change cursor to indicate program is busy
        self._app_main_view.setCursor(Qt.WaitCursor)

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
        log.debug("Thread finished signal received.")

        self._progress_view.hide()
        self._app_main_view.unsetCursor()

        log.debug("Emiting rebuild_tree_signal")
        self.rebuild_tree_signal.emit()

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
        is_apply_changes_enabled = (
            self._is_starting_procedures_allowed
            and not self._app_logic.global_flags.block_normal_procedure
        )
        is_local_install_enabled = (
            self._is_starting_procedures_allowed
            and not self._app_logic.global_flags.block_local_copy_install
        )
        is_software_view_enabled = self._is_packages_selecting_allowed
        is_langs_view_enabled = is_software_view_enabled

        self._app_main_view.button_apply_changes.setEnabled(is_apply_changes_enabled)
        self._app_main_view.button_install_from_local_copy.setEnabled(
            is_local_install_enabled
        )
        self._software_view.setEnabled(is_software_view_enabled)
        self._langs_view.setEnabled(is_langs_view_enabled)

    def _check_system_state(self):
        print("check system state signal emitted")
        self.procedure_thread = ProcedureWorker(
            function_to_run=self._app_logic.check_system_state,
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
