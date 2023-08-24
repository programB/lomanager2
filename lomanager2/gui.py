from pysidecompat import (
    QApplication,  # pyright: ignore
    QCheckBox,  # pyright: ignore
    QDialog,  # pyright: ignore
    QDialogButtonBox,  # pyright: ignore
    QFileDialog,  # pyright: ignore
    QHBoxLayout,  # pyright: ignore
    QLabel,  # pyright: ignore
    QLineEdit,  # pyright: ignore
    QMainWindow,  # pyright: ignore
    QMessageBox,  # pyright: ignore
    QProgressBar,  # pyright: ignore
    QPushButton,  # pyright: ignore
    QTableView,  # pyright: ignore
    QTextEdit,  # pyright: ignore
    QVBoxLayout,  # pyright: ignore
    QWidget,  # pyright: ignore
    QHeaderView,  # pyright: ignore
)
from configuration import logging as log


class AppMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # -- define Software View
        self.software_view = QTableView()
        header = self.software_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # -- end define Main View

        # -- define Languages window
        self.extra_langs_window = LangsModalWindow(parent=self)
        # -- end define Languages window

        # -- define Progress dialog
        self.progress_dialog = ProgressDialog(parent=self)
        # -- end define Progress dialog

        # -- define Apply changes confirmation dialog
        self.confirm_apply_dialog = ConfirmApplyDialog(parent=self)
        # -- end define Apply changes confirmation dialog

        # -- define Local copy install confirmation dialog
        self.confirm_local_copy_dialog = LocalCopyInstallDialog(parent=self)
        # -- end define Local copy install confirmation dialog

        # -- define other GUI elements
        #    (not being real views)
        self.button_install_from_local_copy = QPushButton("Install from local copy")
        self.button_add_langs = QPushButton("Add langs...")
        self.button_apply_changes = QPushButton("Apply changes")
        self.button_quit = QPushButton("Quit")
        self.info_dialog = QMessageBox()
        # -- end define other GUI elements

        main_layout.addWidget(self.button_install_from_local_copy)
        main_layout.addWidget(self.software_view)
        main_layout.addWidget(self.button_add_langs)
        main_layout.addWidget(self.button_apply_changes)
        main_layout.addWidget(self.button_quit)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(900, 550)


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

        # -- define other GUI elements
        flag_OK = QDialogButtonBox.StandardButton.Close
        buttons = flag_OK
        self.buttonBox = QDialogButtonBox(buttons)
        # -- end define other GUI elements
        modal_layout.addWidget(self.langs_view)
        modal_layout.addWidget(self.buttonBox)

        self.setLayout(modal_layout)
        # To close the window some signal has to be emitted.
        # Close button sends reject signal but this not used
        # to take any meaningful actions.
        self.buttonBox.rejected.connect(self.reject)


class ProgressDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("installation progress")
        main_layout = QVBoxLayout()

        self.progress_description = QLabel()
        self.progress_bar = QProgressBar()
        self.overall_progress_description = QLabel()
        self.overall_progress_bar = QProgressBar()
        self.button_terminate = QPushButton("Terminate install (dangerous)!")

        main_layout.addWidget(self.progress_description)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.overall_progress_description)
        main_layout.addWidget(self.overall_progress_bar)
        main_layout.addWidget(self.button_terminate)

        self.setLayout(main_layout)


class ConfirmApplyDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Apply changes")
        main_layout = QVBoxLayout()

        self.info_box = QLabel()
        self.checkbox_keep_packages = QCheckBox("Keep downloaded packages")
        self.checkbox_force_java_download = QCheckBox("Download Java")

        self.buttonBox = QDialogButtonBox()
        self.apply_button = self.buttonBox.addButton(
            QDialogButtonBox.StandardButton.Apply
        )
        self.cancel_button = self.buttonBox.addButton(
            QDialogButtonBox.StandardButton.Cancel
        )

        main_layout.addWidget(self.info_box)
        main_layout.addWidget(self.checkbox_keep_packages)
        main_layout.addWidget(self.checkbox_force_java_download)
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

        self.selected_dir = None

        self.setWindowTitle("Install from local copy")
        main_layout = QVBoxLayout()

        self.info_box = QLabel()

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
        log.debug(
            f"Dialog_returned: {is_selection_made }, selectedFiles: "
            f"{selection_dialog.selectedFiles()} selectedNameFilter: "
            f"{selection_dialog.selectedNameFilter()}"
        )
        if is_selection_made == 1:
            self.directory_choice_box.setText(selection_dialog.selectedFiles()[0])
            self.selected_dir = selection_dialog.selectedFiles()[0]


if __name__ == "__main__":
    app = QApplication()
    window = AppMainWindow()
    window.show()
    app.exec()
