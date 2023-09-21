import gettext
import logging

from .delegates import CheckButtonDelegate
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

        self.setWindowTitle(_("lomanager2"))

        # -- define actions
        self.actions_list = []

        self.actionQuit = ActionsFactory(
            _("Quit"), "application-exit", parent=self, shortcut="Ctrl+Q"
        )
        self.actions_list.append(self.actionQuit)
        self.actionInstallFromLocalCopy = ActionsFactory(
            _("Install from local copy"), "", parent=self
        )
        self.actions_list.append(self.actionInstallFromLocalCopy)
        self.actionHelp = ActionsFactory(
            _("Help"), "system-help", parent=self, shortcut="F1"
        )
        self.actions_list.append(self.actionHelp)
        self.actionAbout = ActionsFactory(_("About"), "", parent=self)
        self.actions_list.append(self.actionAbout)
        self.actionApplyChanges = ActionsFactory(
            _("Apply changes"), "gtk-apply", parent=self
        )
        self.actions_list.append(self.actionApplyChanges)
        self.actionAddLanguages = ActionsFactory(
            _("Add languages"), "set-language", parent=self
        )
        self.actions_list.append(self.actionAddLanguages)

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
        self.info_dialog = QMessageBox(parent=self)

        # -- define documentation dialog
        self.docs_dialog = HelpDialog(parent=self)

        # Get the colors from the current style
        separator_clr = self.palette().color(QPalette.ColorRole.Mid).name()
        window_clr = self.palette().color(QPalette.ColorRole.Window).name()
        # Apply styling to all some children widgets of this window
        stylesheets = [
            f"QLabel#heading {{color: {separator_clr}; text-decoration: underline; qproperty-alignment: AlignLeft}}",
            f"QMainWindow > QToolBar {{border-bottom: 1px solid {separator_clr};}}",
            f"QTableView {{background-color: {window_clr}}}",
            f"QTextEdit {{border: 0 solid black; background-color: {window_clr}}}",
        ]
        self.setStyleSheet("".join(stylesheets))


class CustomTableView(QTableView):
    def __init__(
        self, hide_header: bool = True, no_of_rows: int | None = None, parent=None
    ) -> None:
        super().__init__(parent)

        check_button = CheckButtonDelegate(parent=self)
        self.setItemDelegate(check_button)

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

        self.setWindowTitle(_("Language selection"))
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

        self.setWindowTitle(_("Applying changes"))
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
        # WARNING: Just for tests. This MUST NOT be available to the user
        # main_layout.addWidget(self.button_terminate)

        self.setLayout(main_layout)
        self.setFixedSize(450, 200)

    def showEvent(self, event):
        # This event is called only when the dialog
        # is shown explicitly (on using show() or setVisible(True))
        # Delay using QTimer is used to give OS time to react
        # https://stackoverflow.com/questions/66674305/how-to-center-new-window-relative-to-mainwindow-in-pyqt
        if not event.spontaneous():
            QTimer.singleShot(0, lambda: None)


class ConfirmApplyDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("Confirm changes"))
        main_layout = QVBoxLayout()

        # Small maximum size here because the _scale_info_box method
        # will rescale this window to actual contents size every time
        # the text gets set.
        self.setMaximumHeight(10)
        self.setMaximumWidth(10)

        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        # Allow info_box to expand to its sizeHint minimum
        self.info_box.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )
        self.info_box.textChanged.connect(self._scale_info_box)

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

    def _scale_info_box(self):
        # scale info_box width based on current content.
        # The containing window will not grow vertically with increasing
        # text length but a scrollbar will appear in the info_box.
        self.info_box.setFixedWidth(
            int(
                self.info_box.document().idealWidth()
                + 1.5 * self.info_box.verticalScrollBar().width()
            )
        )
        # readjust the size of the window based on current sizes of
        # child widgets (that is just updated info_box size)
        self.adjustSize()


class LocalCopyInstallDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("Install from local copy"))
        main_layout = QVBoxLayout()

        self.setMaximumHeight(10)
        self.setMaximumWidth(10)
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setLineWrapColumnOrWidth(30)
        self.info_box.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.info_box.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )
        self.info_box.textChanged.connect(self._scale_info_box)

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
        self.selected_dir = QFileDialog.getExistingDirectory(
            self,
            _("Select directory"),
            self.selected_dir,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        self.directory_choice_box.setText(self.selected_dir)

    def _scale_info_box(self):
        # scale info_box width based on current content.
        # The containing this window will not grow vertically with increasing
        # text length but a scrollbar will appear in the info_box.
        w = int(self.info_box.document().idealWidth())
        # w = self.info_box.width()
        self.info_box.setFixedWidth(w)
        # readjust the size of the window based on current sizes of
        # child widgets (that is just updated info_box size)
        self.adjustSize()


class HelpDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(_("Help"))
        modal_layout = QVBoxLayout()

        # -- define text browser
        self.styled_html_view = QTextBrowser()
        self.styled_html_view.setReadOnly(True)
        self.styled_html_view.setOpenExternalLinks(True)
        self.styled_html_view.setOpenLinks(True)

        # -- define other GUI elements
        flag_OK = QDialogButtonBox.StandardButton.Close
        buttons = flag_OK
        self.buttonBox = QDialogButtonBox(buttons)

        modal_layout.addWidget(self.styled_html_view)
        modal_layout.addWidget(self.buttonBox)

        self.setLayout(modal_layout)
        # To close the window some signal has to be emitted.
        # Although close button sends reject signal this is not used
        # to take any meaningful actions.
        self.buttonBox.rejected.connect(self.reject)

        self.markdown_text = ""
        self.html_text = ""
        self.css_text = ""
        self.load_documentation()

        self.resize(640, 480)

    def _load_md(self):
        with open("./docs/help.md", "r") as markdown_f:
            text = markdown_f.read()
        self.markdown_text = text

    def _load_css(self):
        # self.css_text = "body {color: red;}"
        self.css_text = ""

    def _md_to_html(self):
        # convert markdown to html
        document_md = QTextDocument()
        document_md.setMarkdown(self.markdown_text)
        self.html_text = document_md.toHtml()

    def update_view(self):
        # Turn markdown to html
        self._md_to_html()
        # Create empty document and apply css to it
        document_html = QTextDocument()
        document_html.setDefaultStyleSheet(self.css_text)
        # Fill this document with html
        document_html.setHtml(self.html_text)
        # update view
        self.styled_html_view.setDocument(document_html)

    def load_documentation(self):
        self._load_md()
        self._load_css()
        self.update_view()


if __name__ == "__main__":
    app = QApplication()
    window = AppMainWindow()
    window.show()
    app.exec()
