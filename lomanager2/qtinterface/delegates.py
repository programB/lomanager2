import gettext
import logging

from .pysidecompat import *

t = gettext.translation("lomanager2", localedir="./locales", fallback=True)
_ = t.gettext
log = logging.getLogger("lomanager2_logger")

columns = {
    "Program name": {
        "id": 0,
        "i18n_name": _("Program name"),
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
    "language code": {
        "id": 1,
        "i18n_name": _("language code"),
        "show_in_software_view": True,
        "show_in_langs_view": True,
    },
    "language name": {
        "id": 2,
        "i18n_name": _("language name"),
        "show_in_software_view": False,
        "show_in_langs_view": True,
    },
    "version": {
        "id": 3,
        "i18n_name": _("version"),
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
    "marked for removal?": {
        "id": 4,
        "i18n_name": _("marked for removal?"),
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
    "marked for install?": {
        "id": 5,
        "i18n_name": _("marked for install?"),
        "show_in_software_view": True,
        "show_in_langs_view": True,
    },
    "installed?": {
        "id": 6,
        "i18n_name": _("installed?"),
        "show_in_software_view": False,
        "show_in_langs_view": False,
    },
    "marked for download?": {
        "id": 7,
        "i18n_name": _("marked for download?"),
        "show_in_software_view": False,
        "show_in_langs_view": False,
    },
}


class CheckButtonDelegate(QItemDelegate):
    update_model_signal = Signal(QAbstractItemModel, QModelIndex)

    def __init__(self, max_height=40, parent=None):
        super(CheckButtonDelegate, self).__init__(parent)
        self.update_model_signal.connect(self.update_model)
        self.max_button_height = max_height

        # Take colors from current style
        highlight_clr = QWidget().palette().color(QPalette.ColorRole.Highlight)
        text_clr = QWidget().palette().color(QPalette.ColorRole.Text)
        mid_clr = QWidget().palette().color(QPalette.ColorRole.Mid)
        dark_clr = QWidget().palette().color(QPalette.ColorRole.Dark)

        # Color combos (button fill, button border, text)
        self.unchecked_colors = (highlight_clr, text_clr, text_clr)
        self.checked_colors = (text_clr, highlight_clr, highlight_clr)
        self.disabled_colors = (mid_clr, dark_clr, dark_clr)

    def update_model(self, model, index):
        is_visible = bool(index.model().data(index, Qt.ItemDataRole.UserRole + 2))
        if is_visible:
            is_enabled = bool(index.model().data(index, Qt.ItemDataRole.UserRole + 3))
            if is_enabled:
                markstate = index.model().data(index, Qt.ItemDataRole.DisplayRole)
                log.debug(_("≈≈≈≈≈ SETTING DATA BACK TO THE MODEL ≈≈≈≈≈"))
                log.debug(
                    _("switching markstate: {} -> {}").format(markstate, not markstate)
                )
                model.setData(index, not markstate, Qt.ItemDataRole.EditRole)
            else:
                log.debug(_("button disabled"))
        else:
            log.debug(_("button not visible"))

    def editorEvent(self, event, model, option, index):
        is_remove_col = index.column() == columns.get("marked for removal?").get("id")
        is_install_col = index.column() == columns.get("marked for install?").get("id")
        if is_remove_col or is_install_col:
            if (
                isinstance(event, QMouseEvent)
                and event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton
            ) or (
                isinstance(event, QKeyEvent)
                and event.type() == QEvent.Type.KeyPress
                and event.key() == Qt.Key.Key_Space
            ):
                self.update_model_signal.emit(model, index)
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                log.debug(_("mouse double click event"))
                # Capture DoubleClick here
                # (accept event to prevent cell editor getting opened)
                event.accept()
            else:
                # log.debug(f"other editorEvent: {event}")
                # Ignore other events
                pass
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

                is_marked = bool(index.model().data(index, Qt.ItemDataRole.EditRole))
                is_enabled = bool(
                    index.model().data(index, Qt.ItemDataRole.UserRole + 3)
                )
                if is_enabled and is_marked:
                    (btn_clr, btn_border_clr, btn_text_clr) = self.checked_colors
                elif is_enabled and is_marked is False:
                    (btn_clr, btn_border_clr, btn_text_clr) = self.unchecked_colors
                else:
                    (btn_clr, btn_border_clr, btn_text_clr) = self.disabled_colors
                remove_btn_i18n_t = _("remove")
                install_btn_i18n_t = _("install")
                button_text = remove_btn_i18n_t if is_remove_col else install_btn_i18n_t

                #
                painter.save()
                pen = painter.pen()

                full_rect = option.rect.getRect()
                full_x, full_y, full_w, full_h = full_rect

                # Ignore selection: if option.state & QStyle.State_Selected
                # and remove highlight around the button irrespective its
                # selection/focus state
                painter.eraseRect(option.rect)

                # shrink rect slightly
                # delta = 1
                # option.rect.adjust(delta, delta, -delta, -delta)

                # Draw the "button"
                btn_x = full_x
                btn_h = 0.8 * full_h
                btn_y = full_y + (full_h / 2) - (btn_h / 2)
                btn_w = full_w
                # set border color (also controls text color)
                pen.setColor(btn_border_clr)
                painter.setPen(pen)
                # set button fill color
                painter.setBrush(btn_clr)
                #  paint the "button" with smooth edges
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.drawRoundedRect(
                    btn_x, btn_y, btn_w, btn_h, btn_h / 2, btn_h / 2
                )

                # Draw a checkbox
                checkbox_h = 0.6 * btn_h
                checkbox_w = checkbox_h
                margin = checkbox_w
                checkbox_y = btn_y + (btn_h / 2) - (checkbox_h / 2)
                checkbox_x = margin + btn_x
                option.rect.setRect(checkbox_x, checkbox_y, checkbox_w, checkbox_h)
                self.drawCheck(
                    painter,
                    option,
                    option.rect,
                    Qt.CheckState.Checked if is_marked else Qt.CheckState.Unchecked,
                )

                # Draw text
                text_x = checkbox_x + checkbox_w
                text_y = full_y
                text_w = btn_w - (margin + 1.5 * checkbox_w + margin)
                text_h = full_h
                option.rect.setRect(text_x, text_y, text_w, text_h)
                # (re)set pen color to draw text
                pen.setColor(btn_text_clr)
                # pen.setColor("green")
                painter.setPen(pen)
                # Draw button text
                painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, button_text)

                #
                painter.restore()
            else:
                # QtWidgets.QItemDelegate.paint(self, painter, option, index)
                # Do not draw anything - leave the cell empty
                pass
        else:
            # Use default delegates to paint other cells
            QItemDelegate.paint(self, painter, option, index)
