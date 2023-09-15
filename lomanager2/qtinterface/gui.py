import gettext
import logging

from .pysidecompat import *

t = gettext.translation("lomanager2", localedir="./locales", fallback=True)
_ = t.gettext
log = logging.getLogger("lomanager2_logger")


def ActionsFactory(name, icon_theme_name, parent, shortcut=None) -> QAction:
    action = QAction(parent)
    icon = QIcon()
    if QIcon.hasThemeIcon(icon_theme_name):
        icon = QIcon.fromTheme(icon_theme_name)
    else:
        icon.addFile(".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
    action.setIcon(icon)
    action.setText(name)
    if shortcut is not None:
        action.setShortcut(QKeySequence(shortcut))
    return action


class AppMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # -- define actions
        self.actionQuit = ActionsFactory(
            _("Quit"), "application-exit", parent=self, shortcut="Ctrl+Q"
        )
        self.actionInstallFromLocalCopy = ActionsFactory(
            _("Install from local copy"), "", parent=self
        )
        self.actionHelp = ActionsFactory(
            _("Help"), "system-help", parent=self, shortcut="F1"
        )
        self.actionAbout = ActionsFactory(_("About"), "", parent=self)
        self.actionApplyChanges = ActionsFactory(
            _("Apply changes"), "gtk-apply", parent=self
        )
        self.actionAddLanguages = ActionsFactory(
            _("Add languages"), "set-language", parent=self
        )

        # -- define menu bar
        menubar = self.menuBar()
        menuFile = menubar.addMenu(_("&File"))
        menuFile.addAction(self.actionQuit)

        menuTools = menubar.addMenu(_("&Tools"))
        menuTools.addAction(self.actionAddLanguages)
        menuTools.addAction(self.actionApplyChanges)
        menuTools.addAction(self.actionInstallFromLocalCopy)

        menuHelp = menubar.addMenu(_("&Help"))
        menuHelp.addAction(self.actionHelp)
        menuHelp.addAction(self.actionAbout)

        # -- define tool bar
        toolBar = QToolBar()
        toolBar.setMovable(False)
        toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolBar.addAction(self.actionAddLanguages)
        toolBar.addAction(self.actionApplyChanges)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolBar)

        # -- define Software View
        self.office_view = CustomTableView(no_of_rows=5, parent=self)
        self.clipart_view = CustomTableView(no_of_rows=3, parent=self)

        # -- define other GUI elements
        left_spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )

        right_spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        bottom_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        mid_spacer1 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        mid_spacer2 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        office_heading = QLabel("     ")
        office_heading.setObjectName("heading")
        clipart_heading = QLabel("     ")
        clipart_heading.setObjectName("heading")

        # Arrange widgets
        views_layout = QVBoxLayout()
        views_layout.addItem(mid_spacer1)
        views_layout.addWidget(office_heading)
        views_layout.addWidget(self.office_view)
        views_layout.addItem(mid_spacer2)
        views_layout.addWidget(clipart_heading)
        views_layout.addWidget(self.clipart_view)
        views_layout.addItem(bottom_spacer)

        main_layout = QHBoxLayout()
        main_layout.addItem(left_spacer)
        main_layout.addItem(views_layout)
        main_layout.addItem(right_spacer)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        # self.setMinimumSize(700, 550)

        # -- define Languages window
        self.extra_langs_window = LangsModalWindow(parent=self)

        # -- define Progress dialog
        self.progress_dialog = ProgressDialog(parent=self)

        # -- define Apply changes confirmation dialog
        self.confirm_apply_dialog = ConfirmApplyDialog(parent=self)

        # -- define Local copy install confirmation dialog
        self.confirm_local_copy_dialog = LocalCopyInstallDialog(parent=self)

        # -- define info dialog
        self.info_dialog = QMessageBox()

        # Get the colors from the current style
        separator_clr = self.palette().color(QPalette.ColorRole.Mid).name()
        window_clr = self.palette().color(QPalette.ColorRole.Window).name()
        # Apply styling to all some children widgets of this window
        stylesheets = [
            f"QLabel#heading {{color: {separator_clr}; text-decoration: underline; qproperty-alignment: AlignLeft}}",
            f"QMainWindow > QToolBar {{border-bottom: 1px solid {separator_clr};}}",
            f"QTableView {{background-color: {window_clr}}}",
        ]
        self.setStyleSheet("".join(stylesheets))


class CustomTableView(QTableView):
    def __init__(
        self, hide_header: bool = True, no_of_rows: int | None = None, parent=None
    ) -> None:
        super().__init__(parent)

        # Number of rows to be displayed before scrollbar appears
        self.no_of_rows = no_of_rows

        # horizontal header is defined but for proper UX should be hidden,
        # (with the exception of langs_view which can pass
        #  hide_header=False for that purpose)
        #  table should resize to its size automatically
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        #
        if hide_header:
            self.horizontalHeader().hide()

        # Vertical header should not exist at all
        self.verticalHeader().hide()

        # Selection and focus should be turned off
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.setShowGrid(False)

        # Table should not change its size when containing window is resized
        main_views_size_policy = QSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        main_views_size_policy.setRetainSizeWhenHidden(True)
        lang_view_size_policy = QSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding
        )
        lang_view_size_policy.setRetainSizeWhenHidden(True)
        self.setSizePolicy(
            lang_view_size_policy if no_of_rows is None else main_views_size_policy
        )

        # Never show horizontal scrollbar
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Remove frame
        self.setFrameShape(QFrame.Shape.NoFrame)

    def sizeHint(self):
        col_width_sum = 0
        for i in range(self.model().columnCount()):
            if not self.isColumnHidden(i):
                col_width_sum += self.columnWidth(i)
        scroll_bar_width = self.style().pixelMetric(
            QStyle.PixelMetric.PM_ScrollBarExtent
        )

        table_size = super().sizeHint()  # get current size
        # Override width (added 2x scroll_bar_width for nicer look)
        table_size.setWidth(col_width_sum + 2 * scroll_bar_width)
        if self.no_of_rows is not None:
            # Set table height hint to requested muliple of rowHeight
            table_size.setHeight(self.no_of_rows * self.rowHeight(0))
        else:
            # Unrestricted number of rows. That means it's a langs_view
            # and since the width was already set by setWidth above
            # the containing window (parent of langs_view)
            # should be fixed in its horizontal size.
            # (The user can expand that window verticaly though and also
            #  the scrollbar will be shown if needed)
            self.parent().setFixedWidth(table_size.width())
        return table_size

    def paintEvent(self, event):
        self.updateGeometry()  # checks sizeHint
        super().paintEvent(event)


class LangsModalWindow(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("language selection window"))
        modal_layout = QVBoxLayout()

        # -- define Langs View
        self.langs_view = CustomTableView(hide_header=False, parent=self)
        # Allow columns to be user sortable
        # (model to which this view will get attached decides which
        #  column(s) are keyed for sorting)
        self.langs_view.setSortingEnabled(True)

        # -- define other GUI elements
        flag_OK = QDialogButtonBox.StandardButton.Close
        buttons = flag_OK
        self.buttonBox = QDialogButtonBox(buttons)

        modal_layout.addWidget(self.langs_view)
        modal_layout.addWidget(self.buttonBox)

        self.setLayout(modal_layout)
        # To close the window some signal has to be emitted.
        # Although close button sends reject signal this is not used
        # to take any meaningful actions.
        self.buttonBox.rejected.connect(self.reject)


class ProgressDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("installation progress"))
        main_layout = QVBoxLayout()

        self.progress_description = QLabel()
        self.progress_bar = QProgressBar()
        self.overall_progress_description = QLabel()
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setFormat("%v / %m")
        self.button_terminate = QPushButton(_("Terminate install (dangerous)!"))

        main_layout.addWidget(self.progress_description)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.overall_progress_description)
        main_layout.addWidget(self.overall_progress_bar)
        main_layout.addWidget(self.button_terminate)

        self.setLayout(main_layout)


class ConfirmApplyDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("Confirm changes"))
        main_layout = QVBoxLayout()

        self.info_box = QLabel()
        self.checkbox_keep_packages = QCheckBox(_("Keep downloaded packages"))
        self.checkbox_force_java_download = QCheckBox(_("Download Java"))
        # Initially disabled !
        self.checkbox_force_java_download.setEnabled(False)

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


class LocalCopyInstallDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("Install from local copy"))
        main_layout = QVBoxLayout()

        self.info_box = QLabel()
        self.info_box.setWordWrap(True)

        file_input_layout = QHBoxLayout()
        self.directory_choice_box = QLineEdit()
        self.directory_choice_box.setReadOnly(True)
        self.button_choose_directory = QPushButton(_("Choose directory..."))
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
        selection_dialog = QFileDialog()
        caption = "Select directory"
        selection_dialog.setWindowTitle(caption)
        selection_dialog.setDirectory(self.selected_dir)
        selection_dialog.setFileMode(QFileDialog.FileMode.Directory)

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
    app = QApplication()
    window = AppMainWindow()
    window.show()
    app.exec()
