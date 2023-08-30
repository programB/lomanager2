from pysidecompat import QtGui, QtWidgets, QtCore  # pyright: ignore
from configuration import logging as log

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
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
    "marked for download?": {
        "id": 7,
        "show_in_software_view": True,
        "show_in_langs_view": False,
    },
}


class PushButtonDelegate(QtWidgets.QItemDelegate):
    update_model_signal = QtCore.Signal(QtCore.QAbstractItemModel, QtCore.QModelIndex)

    def __init__(self, parent=None):
        super(PushButtonDelegate, self).__init__(parent)
        self.update_model_signal.connect(self.update_model)

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
                model.setData(
                    index, str(not markstate), QtCore.Qt.ItemDataRole.EditRole
                )
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
                painter.save()

                markstate = bool(
                    index.model().data(index, QtCore.Qt.ItemDataRole.EditRole)
                )
                is_enabled = bool(
                    index.model().data(index, QtCore.Qt.ItemDataRole.UserRole + 3)
                )

                normal_button_color = QtGui.QColor("green")
                normal_button_border_color = QtGui.QColor("dark green")
                normal_text_color = QtGui.QColor("white")

                disabled_button_color = QtGui.QColor("#635f5e")
                disabled_button_border_color = QtGui.QColor("#484544")
                disabled_text_color = QtGui.QColor("#b4adaa")

                # Ignore the check: if option.state & QStyle.State_Selected
                # and remove highlight around the button irrespective its
                # selection/focus state
                painter.eraseRect(option.rect)

                # controls border color (and text color)
                pen = painter.pen()
                pen.setColor(
                    normal_button_border_color
                    if is_enabled
                    else disabled_button_border_color
                )
                painter.setPen(pen)

                # controls the fill color
                painter.setBrush(
                    normal_button_color if is_enabled else disabled_button_color
                )

                # Draw the "button"
                delta = 2
                option.rect.adjust(delta, delta, -delta, -delta)
                x, y, w, h = option.rect.getRect()
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.drawRoundedRect(x, y, w, h, 10, 10)

                # change pen color to draw text
                pen.setColor(normal_text_color if is_enabled else disabled_text_color)
                painter.setPen(pen)
                button_text = "remove" if is_remove_col else "install"
                painter.drawText(
                    option.rect, QtCore.Qt.AlignmentFlag.AlignCenter, button_text
                )

                # draw a checkbox
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
                    QtCore.Qt.Checked if markstate else QtCore.Qt.Unchecked,
                )
                painter.restore()
            else:
                # QtWidgets.QItemDelegate.paint(self, painter, option, index)
                # Do not draw anything - leave the cell empty
                pass
        else:
            # Use default delegates to paint other cells
            QtWidgets.QItemDelegate.paint(self, painter, option, index)
