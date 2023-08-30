from pysidecompat import QtGui, QtWidgets, QtCore  # pyright: ignore
from configuration import logging as log


class AppMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()

        # -- define Software View
        self.software_view = QtWidgets.QTableView()
        header = self.software_view.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
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
        self.button_install_from_local_copy = QtWidgets.QPushButton(
            "Install from local copy"
        )
        self.button_add_langs = QtWidgets.QPushButton("Add langs...")
        self.button_apply_changes = QtWidgets.QPushButton("Apply changes")
        self.button_quit = QtWidgets.QPushButton("Quit")
        self.info_dialog = QtWidgets.QMessageBox()
        # -- end define other GUI elements

        main_layout.addWidget(self.button_install_from_local_copy)
        main_layout.addWidget(self.software_view)
        main_layout.addWidget(self.button_add_langs)
        main_layout.addWidget(self.button_apply_changes)
        main_layout.addWidget(self.button_quit)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(900, 550)


class LangsModalWindow(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("language selection window")
        modal_layout = QtWidgets.QVBoxLayout()

        # -- define Langs View
        self.langs_view = QtWidgets.QTableView()
        header = self.langs_view.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # Allow columns to be user sortable
        # (model to which this view will get attached decides which
        #  column(s) are keyed for sorting)
        self.langs_view.setSortingEnabled(True)
        # -- end define Langs View

        # -- define other GUI elements
        flag_OK = QtWidgets.QDialogButtonBox.StandardButton.Close
        buttons = flag_OK
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        # -- end define other GUI elements
        modal_layout.addWidget(self.langs_view)
        modal_layout.addWidget(self.buttonBox)

        self.setLayout(modal_layout)
        # To close the window some signal has to be emitted.
        # Close button sends reject signal but this not used
        # to take any meaningful actions.
        self.buttonBox.rejected.connect(self.reject)


class ProgressDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("installation progress")
        main_layout = QtWidgets.QVBoxLayout()

        self.progress_description = QtWidgets.QLabel()
        self.progress_bar = QtWidgets.QProgressBar()
        self.overall_progress_description = QtWidgets.QLabel()
        self.overall_progress_bar = QtWidgets.QProgressBar()
        self.button_terminate = QtWidgets.QPushButton("Terminate install (dangerous)!")

        main_layout.addWidget(self.progress_description)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.overall_progress_description)
        main_layout.addWidget(self.overall_progress_bar)
        main_layout.addWidget(self.button_terminate)

        self.setLayout(main_layout)


class ConfirmApplyDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Apply changes")
        main_layout = QtWidgets.QVBoxLayout()

        self.info_box = QtWidgets.QLabel()
        self.checkbox_keep_packages = QtWidgets.QCheckBox("Keep downloaded packages")
        self.checkbox_force_java_download = QtWidgets.QCheckBox("Download Java")

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.apply_button = self.buttonBox.addButton(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        )
        self.cancel_button = self.buttonBox.addButton(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
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


class LocalCopyInstallDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.selected_dir = None

        self.setWindowTitle("Install from local copy")
        main_layout = QtWidgets.QVBoxLayout()

        self.info_box = QtWidgets.QLabel()

        file_input_layout = QtWidgets.QHBoxLayout()
        self.initial_dir = "/"
        self.directory_choice_box = QtWidgets.QLineEdit()
        self.directory_choice_box.setReadOnly(True)
        self.directory_choice_box.setPlaceholderText(self.initial_dir)
        self.button_choose_directory = QtWidgets.QPushButton("Choose directory...")
        file_input_layout.addWidget(self.directory_choice_box)
        file_input_layout.addWidget(self.button_choose_directory)

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.apply_button = self.buttonBox.addButton(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        )
        self.cancel_button = self.buttonBox.addButton(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
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

        selection_dialog = QtWidgets.QFileDialog()
        selection_dialog.setWindowTitle(caption)
        selection_dialog.setDirectory(self.initial_dir)
        selection_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)

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
    app = QtWidgets.QApplication()
    window = AppMainWindow()
    window.show()
    app.exec()
