from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)


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

        # -- define other GUI elements
        #    (not belonging to Main View or Languages View)
        self.button_refresh = QPushButton("Refresh")
        self.button_add_langs = QPushButton("Add langs...")
        self.button_apply_changes = QPushButton("Apply changes")
        self.button_quit = QPushButton("Quit")
        # -- end define other GUI elements

        main_layout.addWidget(self.button_refresh)
        main_layout.addWidget(self.package_menu_view)
        main_layout.addWidget(self.button_add_langs)
        main_layout.addWidget(self.button_apply_changes)
        main_layout.addWidget(self.button_quit)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(900, 550)

    def open_langs_selection_modal_window(self, s):
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


if __name__ == "__main__":
    app = QApplication()
    window = AppMainWindow()
    window.show()
    app.exec()
