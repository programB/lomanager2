from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
import configuration


class AppMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # -- define Main View
        self.package_menu_view = QTableView()
        header = self.package_menu_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # -- end define Main View

        # -- define Languages View
        self.extra_langs_view = LangsModalWindow(parent=self)
        # -- end define Languages View

        # -- define Progress dialog
        self.progress_view = ProgressDialog(parent=self)
        # -- end define Progress dialog

        # -- define Apply changes confirmation dialog
        self.confirm_apply_view = ConfirmApplyDialog(parent=self)
        # -- end define Apply changes confirmation dialog

        # -- define Local copy install confirmation dialog
        self.confirm_local_copy_view = LocalCopyInstallDialog(parent=self)
        # -- end define Local copy install confirmation dialog

        # -- define other GUI elements
        #    (not belonging to Main View or Languages View)
        self.button_install_from_local_copy = QPushButton("Install from local copy")
        self.button_add_langs = QPushButton("Add langs...")
        self.button_apply_changes = QPushButton("Apply changes")
        self.button_quit = QPushButton("Quit")
        self.info_dialog = QMessageBox()
        # -- end define other GUI elements

        main_layout.addWidget(self.button_install_from_local_copy)
        main_layout.addWidget(self.package_menu_view)
        main_layout.addWidget(self.button_add_langs)
        main_layout.addWidget(self.button_apply_changes)
        main_layout.addWidget(self.button_quit)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(900, 550)

    def open_langs_selection_modal_window(self):
        self.extra_langs_view.exec()


class LangsModalWindow(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("language selection window")
        modal_layout = QVBoxLayout()

        # -- define Langs View
        self.langs_view = QTableView()
        header = self.langs_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # -- end define Langs View

        # -- define other GUI elements (not belonging to Langs View)
        flag_OK = QDialogButtonBox.StandardButton.Ok
        flag_Cancel = QDialogButtonBox.StandardButton.Cancel
        buttons = flag_OK | flag_Cancel
        self.buttonBox = QDialogButtonBox(buttons)
        # -- end define other GUI elements (not belonging to Langs View)
        modal_layout.addWidget(self.langs_view)
        modal_layout.addWidget(self.buttonBox)

        self.setLayout(modal_layout)
        # TODO: should this be connected in the Adapter?
        # TODO: how to handle user pressing Cancel ?
        #       The viewmodel will pass selections made to the
        #       model/logic the moment user clicks the checkboxes
        #       in the table without waiting for any confirmation
        #       button being clicked.
        #       One way would be to replace this OK|Cancel
        #       with just OK. User would then have to deselect
        #       whatever he selected to go back to original state
        #       of selections rather then Cancel button providing
        #       this function for him (but this is kind of cheating).
        #       Other solution is to make some kind of copy/buffer
        #       of the selection and show this to the user instead
        #       of the view connected to the viewmodel.
        #       Then upon clicking the buffer will be passed/(replayed
        #       element by element onto the viewmodel)
        #       Cancel will simply clear the buffer without
        #       involving viewmodel.
        #       But where to put this logic?
        #       - In the adapter?
        #       - in the viewmodel (how then to route the signals there)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


class ProgressDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("installation progress")
        main_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.button_terminate = QPushButton("Terminate install (dangerous)!")

        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.button_terminate)

        self.setLayout(main_layout)


class ConfirmApplyDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Apply changes")
        main_layout = QVBoxLayout()

        self.info_box = QTextEdit()
        self.checkbox_keep_packages = QCheckBox("Keep downloaded packages")

        self.buttonBox = QDialogButtonBox()
        self.apply_button = self.buttonBox.addButton(
            QDialogButtonBox.StandardButton.Apply
        )
        self.cancel_button = self.buttonBox.addButton(
            QDialogButtonBox.StandardButton.Cancel
        )

        main_layout.addWidget(self.info_box)
        main_layout.addWidget(self.checkbox_keep_packages)
        main_layout.addWidget(self.buttonBox)

        self.setLayout(main_layout)

        # Cancel button sends this so we can connect directly
        self.buttonBox.rejected.connect(self.reject)
        # Apply button sends something else so we will
        # check which button was pressed and ...
        self.buttonBox.clicked.connect(self._which_button)
        self.buttonBox.accepted.connect(self.accept)

    def _which_button(self, clicked_button):
        # ... if it is apply button we will make it
        #     send the 'accepted' signal
        if clicked_button is self.apply_button:
            self.buttonBox.accepted.emit()


class LocalCopyInstallDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Install from local copy")
        main_layout = QVBoxLayout()

        # PAGE 128
        self.info_box = QTextEdit()

        file_input_layout = QHBoxLayout()
        self.initial_dir = "/"
        self.directory_choice_box = QLineEdit()
        self.directory_choice_box.setReadOnly(True)
        self.directory_choice_box.setPlaceholderText(self.initial_dir)
        self.button_choose_directory = QPushButton("Choose directory...")
        file_input_layout.addWidget(self.directory_choice_box)
        file_input_layout.addWidget(self.button_choose_directory)

        self.buttonBox = QDialogButtonBox()
        self.apply_button = self.buttonBox.addButton(
            QDialogButtonBox.StandardButton.Apply
        )
        self.cancel_button = self.buttonBox.addButton(
            QDialogButtonBox.StandardButton.Cancel
        )

        main_layout.addWidget(self.info_box)
        main_layout.addItem(file_input_layout)
        main_layout.addWidget(self.buttonBox)

        self.setLayout(main_layout)

        self.button_choose_directory.clicked.connect(self._chose_directory)

        # Cancel button sends this so we can connect directly
        self.buttonBox.rejected.connect(self.reject)
        # Apply button sends something else so we will
        # check which button was pressed and ...
        self.buttonBox.clicked.connect(self._which_button)
        self.buttonBox.accepted.connect(self.accept)

    def _which_button(self, clicked_button):
        # ... if it is the apply button we will
        #     emit the 'accepted' signal that is connected
        #     to the accept slot.
        if clicked_button is self.apply_button:
            self.buttonBox.accepted.emit()

    def _chose_directory(self):
        caption = "Select directory"

        selection_dialog = QFileDialog()
        selection_dialog.setWindowTitle(caption)
        selection_dialog.setDirectory(self.initial_dir)
        selection_dialog.setFileMode(QFileDialog.FileMode.Directory)

        is_selection_made = selection_dialog.exec()
        configuration.logging.debug(
            f"Dialog_returned: {is_selection_made }, selectedFiles: "
            f"{selection_dialog.selectedFiles()} selectedNameFilter: "
            f"{selection_dialog.selectedNameFilter()}"
        )
        if is_selection_made == 1:
            self.directory_choice_box.setText(selection_dialog.selectedFiles()[0])


if __name__ == "__main__":
    app = QApplication()
    window = AppMainWindow()
    window.show()
    app.exec()
