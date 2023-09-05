from pysidecompat import QtGui, QtWidgets, QtCore  # pyright: ignore
import logging

log = logging.getLogger("lomanager2_logger")

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
        "show_in_software_view": False,
        "show_in_langs_view": False,
    },
    "marked for download?": {
        "id": 7,
        "show_in_software_view": False,
        "show_in_langs_view": False,
    },
}


class CheckButtonDelegate(QtWidgets.QItemDelegate):
    update_model_signal = QtCore.Signal(QtCore.QAbstractItemModel, QtCore.QModelIndex)

    checked_button_color = QtGui.QColor("#005b00")  # dark green
    checked_button_border_color = QtGui.QColor("#005b00")  # dark green
    unchecked_button_color = QtGui.QColor("#008000")  # green
    unchecked_button_border_color = QtGui.QColor("#008000")  # green
    disabled_button_color = QtGui.QColor("#635f5e")  # mid grey
    disabled_button_border_color = QtGui.QColor("#484544")  # dark grey
    normal_text_color = QtGui.QColor("white")
    disabled_text_color = QtGui.QColor("#b4adaa")  # light grey

    def __init__(self, max_height=40, parent=None):
        super(CheckButtonDelegate, self).__init__(parent)
        self.update_model_signal.connect(self.update_model)
        self.max_button_height = max_height

    def update_model(self, model, index):
        is_visible = bool(
            index.model().data(index, QtCore.Qt.ItemDataRole.UserRole + 2)
        )
        if is_visible:
            is_enabled = bool(
                index.model().data(index, QtCore.Qt.ItemDataRole.UserRole + 3)
            )
            if is_enabled:
                markstate = index.model().data(
                    index, QtCore.Qt.ItemDataRole.DisplayRole
                )
                log.debug("≈≈≈≈≈ SETTING DATA BACK TO THE MODEL ≈≈≈≈≈")
                log.debug(f"switching markstate: {markstate} -> {not markstate}")
                model.setData(index, not markstate, QtCore.Qt.ItemDataRole.EditRole)
            else:
                log.debug("button disabled")
        else:
            log.debug("button not visible")

    def editorEvent(self, event, model, option, index):
        is_remove_col = index.column() == columns.get("marked for removal?").get("id")
        is_install_col = index.column() == columns.get("marked for install?").get("id")
        if is_remove_col or is_install_col:
            if (
                event.type() == QtCore.QEvent.Type.MouseButtonRelease
                and event.button() == QtCore.Qt.MouseButton.LeftButton
            ) or (
                event.type() == QtCore.QEvent.Type.KeyPress
                and event.key() == QtCore.Qt.Key.Key_Space
            ):
                self.update_model_signal.emit(model, index)
            elif event.type() == QtCore.QEvent.Type.MouseButtonDblClick:
                log.debug("2-clicked MOUSE")
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
            is_visible = bool(
                index.model().data(index, QtCore.Qt.ItemDataRole.UserRole + 2)
            )
            if is_visible:
                # Do the button painting here

                is_marked = bool(
                    index.model().data(index, QtCore.Qt.ItemDataRole.EditRole)
                )
                is_enabled = bool(
                    index.model().data(index, QtCore.Qt.ItemDataRole.UserRole + 3)
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
                button_text = "remove" if is_remove_col else "install"

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
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.drawRoundedRect(x, y, w, h, 10, 10)

                # (re)set pen color to draw text
                pen.setColor(button_text_color)
                painter.setPen(pen)

                # Draw button text
                painter.drawText(
                    option.rect, QtCore.Qt.AlignmentFlag.AlignCenter, button_text
                )

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
                    QtCore.Qt.Checked if is_marked else QtCore.Qt.Unchecked,
                )

                #
                painter.restore()
            else:
                # QtWidgets.QItemDelegate.paint(self, painter, option, index)
                # Do not draw anything - leave the cell empty
                pass
        else:
            # Use default delegates to paint other cells
            QtWidgets.QItemDelegate.paint(self, painter, option, index)
