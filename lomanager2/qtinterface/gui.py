import gettext
import logging

from .pysidecompat import QtCore, QtGui, QtWidgets  # pyright: ignore

t = gettext.translation("lomanager2", localedir="./locales", fallback=True)
_ = t.gettext
log = logging.getLogger("lomanager2_logger")


class AppMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()

        # -- define Software View
        self.software_view = QtWidgets.QTableView()
        header = self.software_view.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # Header is defined but for proper UX should be hidden in this view
        self.software_view.verticalHeader().hide()
        self.software_view.horizontalHeader().hide()
        # Selection and focus should be turned off in this view for UX reasons
        self.software_view.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.NoSelection
        )
        self.software_view.setFocusPolicy(QtGui.Qt.NoFocus)
        # Hide grid for better UX
        self.software_view.setShowGrid(False)

        # -- define Languages window
        self.extra_langs_window = LangsModalWindow(parent=self)

        # -- define Progress dialog
        self.progress_dialog = ProgressDialog(parent=self)

        # -- define Apply changes confirmation dialog
        self.confirm_apply_dialog = ConfirmApplyDialog(parent=self)

        # -- define Local copy install confirmation dialog
        self.confirm_local_copy_dialog = LocalCopyInstallDialog(parent=self)

        # -- define other GUI elements
        self.button_install_from_local_copy = QtWidgets.QPushButton(
            _("Install from local copy")
        )
        self.button_add_langs = QtWidgets.QPushButton(_("Add langs..."))
        self.button_apply_changes = QtWidgets.QPushButton(_("Appy changes"))
        self.button_quit = QtWidgets.QPushButton(_("Quit"))
        self.info_dialog = QtWidgets.QMessageBox()

        main_layout.addWidget(self.button_install_from_local_copy)
        main_layout.addWidget(self.software_view)
        main_layout.addWidget(self.button_add_langs)
        main_layout.addWidget(self.button_apply_changes)
        main_layout.addWidget(self.button_quit)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(700, 550)


class LangsModalWindow(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("language selection window"))
        modal_layout = QtWidgets.QVBoxLayout()

        # -- define Langs View
        self.langs_view = QtWidgets.QTableView()
        header = self.langs_view.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # Allow columns to be user sortable
        # (model to which this view will get attached decides which
        #  column(s) are keyed for sorting)
        self.langs_view.setSortingEnabled(True)

        # -- define other GUI elements
        flag_OK = QtWidgets.QDialogButtonBox.StandardButton.Close
        buttons = flag_OK
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)

        modal_layout.addWidget(self.langs_view)
        modal_layout.addWidget(self.buttonBox)

        self.setLayout(modal_layout)
        # To close the window some signal has to be emitted.
        # Although close button sends reject signal this is not used
        # to take any meaningful actions.
        self.buttonBox.rejected.connect(self.reject)


class ProgressDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("installation progress"))
        main_layout = QtWidgets.QVBoxLayout()

        self.progress_description = QtWidgets.QLabel()
        self.progress_bar = QtWidgets.QProgressBar()
        self.overall_progress_description = QtWidgets.QLabel()
        self.overall_progress_bar = QtWidgets.QProgressBar()
        self.overall_progress_bar.setFormat("%v / %m")
        self.button_terminate = QtWidgets.QPushButton(
            _("Terminate install (dangerous)!")
        )

        main_layout.addWidget(self.progress_description)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.overall_progress_description)
        main_layout.addWidget(self.overall_progress_bar)
        main_layout.addWidget(self.button_terminate)

        self.setLayout(main_layout)


class ConfirmApplyDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("Confirm changes"))
        main_layout = QtWidgets.QVBoxLayout()

        self.info_box = QtWidgets.QLabel()
        self.checkbox_keep_packages = QtWidgets.QCheckBox(_("Keep downloaded packages"))
        self.checkbox_force_java_download = QtWidgets.QCheckBox(_("Download Java"))
        # Initially disabled !
        self.checkbox_force_java_download.setEnabled(False)

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

        self.checkbox_keep_packages.stateChanged.connect(self._offer_java)
        # Cancel button sends rejected signal so it can be connected directly
        self.buttonBox.rejected.connect(self.reject)
        # Apply button is not sending accepted signal but something else.
        # Check which button was pressed and ...
        self.buttonBox.clicked.connect(self._which_button)
        self.buttonBox.accepted.connect(self.accept)

    def _which_button(self, clicked_button):
        # ... if it's the apply button send the 'accepted' signal
        if clicked_button is self.apply_button:
            self.buttonBox.accepted.emit()

    def _offer_java(self, is_keep_packages_marked):
        self.checkbox_force_java_download.setEnabled(is_keep_packages_marked)


class LocalCopyInstallDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("Install from local copy"))
        main_layout = QtWidgets.QVBoxLayout()

        self.info_box = QtWidgets.QLabel()
        self.info_box.setWordWrap(True)

        file_input_layout = QtWidgets.QHBoxLayout()
        self.directory_choice_box = QtWidgets.QLineEdit()
        self.directory_choice_box.setReadOnly(True)
        self.button_choose_directory = QtWidgets.QPushButton(_("Choose directory..."))
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
        # Apply button is not sending accepted signal but something else.
        # Check which button was pressed and ...
        self.buttonBox.clicked.connect(self._which_button)
        self.buttonBox.accepted.connect(self.accept)

        self.set_initial_dir()

    def _which_button(self, clicked_button):
        # ... if it's the apply button send the 'accepted' signal
        if clicked_button is self.apply_button:
            self.buttonBox.accepted.emit()

    def set_initial_dir(self, dir: str | None = None) -> None:
        # Set some initial value - it will be overridden by user selection
        self.selected_dir = "/" if dir is None else dir
        self.directory_choice_box.setText("")
        self.directory_choice_box.setPlaceholderText(self.selected_dir)

    def _chose_directory(self):
        selection_dialog = QtWidgets.QFileDialog()
        caption = "Select directory"
        selection_dialog.setWindowTitle(caption)
        selection_dialog.setDirectory(self.selected_dir)
        selection_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)

        is_selection_made = selection_dialog.exec()
        log.debug(
            _("Dialog_returned: {}, selectedFiles: {} selectedNameFilter: {}").format(
                is_selection_made,
                selection_dialog.selectedFiles(),
                selection_dialog.selectedNameFilter(),
            )
        )
        if is_selection_made == 1:
            self.directory_choice_box.setText(selection_dialog.selectedFiles()[0])
            self.selected_dir = selection_dialog.selectedFiles()[0]


if __name__ == "__main__":
    app = QtWidgets.QApplication()
    window = AppMainWindow()
    window.show()
    app.exec()
