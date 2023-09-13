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

    checked_button_color = QColor("#005b00")  # dark green
    checked_button_border_color = QColor("#005b00")  # dark green
    unchecked_button_color = QColor("#008000")  # green
    unchecked_button_border_color = QColor("#008000")  # green
    disabled_button_color = QColor("#635f5e")  # mid grey
    disabled_button_border_color = QColor("#484544")  # dark grey
    normal_text_color = QColor("white")
    disabled_text_color = QColor("#b4adaa")  # light grey

    def __init__(self, max_height=40, parent=None):
        super(CheckButtonDelegate, self).__init__(parent)
        self.update_model_signal.connect(self.update_model)
        self.max_button_height = max_height

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
                    button_color = self.checked_button_color
                    button_border_color = self.checked_button_border_color
                    button_text_color = self.normal_text_color
                elif is_enabled and is_marked is False:
                    button_color = self.unchecked_button_color
                    button_border_color = self.unchecked_button_border_color
                    button_text_color = self.normal_text_color
                else:
                    button_color = self.disabled_button_color
                    button_border_color = self.disabled_button_border_color
                    button_text_color = self.disabled_text_color
                remove_btn_i18n_t = _("remove")
                install_btn_i18n_t = _("install")
                button_text = remove_btn_i18n_t if is_remove_col else install_btn_i18n_t

                #
                painter.save()

                # Ignore selection: if option.state & QStyle.State_Selected
                # and remove highlight around the button irrespective its
                # selection/focus state
                painter.eraseRect(option.rect)

                # set border color (also controls text color)
                pen = painter.pen()
                pen.setColor(button_border_color)
                painter.setPen(pen)

                # set button fill color
                painter.setBrush(button_color)

                # Draw the "button"
                # limit button height
                x, y, w, h = option.rect.getRect()
                new_h = self.max_button_height if h > self.max_button_height else h
                new_y = y + (h / 2) - (new_h / 2)
                option.rect.setRect(x, new_y, w, new_h)

                # shrink is slightly
                delta = 2
                option.rect.adjust(delta, delta, -delta, -delta)
                x, y, w, h = option.rect.getRect()

                # paint with smooth edges
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.drawRoundedRect(x, y, w, h, 10, 10)

                # (re)set pen color to draw text
                pen.setColor(button_text_color)
                painter.setPen(pen)

                # Draw button text
                painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, button_text)

                # Draw a checkbox
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
                    Qt.CheckState.Checked if is_marked else Qt.CheckState.Unchecked,
                )

                #
                painter.restore()
            else:
                # QtWidgets.QItemDelegate.paint(self, painter, option, index)
                # Do not draw anything - leave the cell empty
                pass
        else:
            # Use default delegates to paint other cells
            QItemDelegate.paint(self, painter, option, index)
