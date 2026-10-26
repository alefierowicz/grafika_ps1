GRID_SIZE=50
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtWidgets import QMenu

from shapes import *

MENU_STYLE = """
    QMenu {
        background-color: #1f2630;
        border: 1px solid #323d4b;
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item {
        color: #dce3ec;
        padding: 5px 24px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #f08a24;
        color: #1e242c;
    }
    QMenu::item:disabled {
        color: #f08a24;
    }
    QMenu::separator {
        height: 1px;
        background: #323d4b;
        margin: 4px 8px;
    }
"""

CLICK_DRAW_STYLE = """
    QMenu { border: 2px solid #f08a24; }
"""

class Canvas(QWidget):
    selection_changed = Signal(object)  # the newly selected shape, or None
    shape_edited = Signal()             # the selected shape was moved/reshaped by the mouse

    def __init__(self):
        super().__init__()
        self.setFixedSize(900,700)
        self.setMouseTracking(True)

        self.preview = None
        self.pending = None # ctrl click initiated state

        self.dragging = None  # shape being moved with the mouse
        self.drag_last = None # cursor position at the previous move event

        self.selected = None     # shape showing its handles
        self.handle_drag = None  # index of the selected shape's handle being dragged

        self.shapes = []
        self.pen = QPen(QColor("black"), 2) # default style

    def set_selected(self, shape):
        # the only place that changes the selection, so the signal is never forgotten
        if shape is not self.selected:
            self.selected = shape
            self.selection_changed.emit(shape)
        self.update()

    def is_drawing(self):
        return self.preview is not None or self.pending is not None

    def shape_at(self, point):
        # topmost first: the last drawn shape is painted on top
        for shape in reversed(self.shapes):
            if shape.hit_test(point):
                return shape
        return None

    def open_shape_menu(self, shape, event):
        # right-clicking a shape also selects it, so you can see what the menu acts on
        self.set_selected(shape)

        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        delete_action = menu.addAction("delete")

        chosen = menu.exec(event.globalPosition().toPoint())
        if chosen == delete_action:
            self.shapes.remove(shape)
            self.set_selected(None)
            self.unsetCursor()
            self.update()

    def open_menu(self, event):
        start = event.position()

        # right-click on a shape's edge gets the shape menu instead
        if not self.is_drawing():
            shape = self.shape_at(start)
            if shape:
                self.open_shape_menu(shape, event)
                return


        click_mode = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        
        menu = QMenu(self)

        if click_mode:
            menu.setStyleSheet(MENU_STYLE + CLICK_DRAW_STYLE)
            menu.addAction("click-draw").setEnabled(False)
            menu.addSeparator()
        else:
            menu.setStyleSheet(MENU_STYLE)
            
        line_action = menu.addAction("line")
        rect_action = menu.addAction("rectangle")
        circle_action = menu.addAction("circle")
        
        menu.addSeparator()
        clear_action = menu.addAction("clear all")

        shape_type = None
        chosen = menu.exec(event.globalPosition().toPoint())

        if chosen == line_action:
            shape_type = Line
        elif chosen == rect_action:
            shape_type = Rectangle
        elif chosen == circle_action:
            shape_type = Circle
        elif chosen == clear_action:
            self.shapes.clear()
            self.set_selected(None)
            self.preview = None
            self.pending = None
            self.unsetCursor()

        if shape_type:
            self.set_selected(None)  # drawing something new: drop the selection

        if click_mode and shape_type:
            self.pending = shape_type
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif shape_type:
            self.preview = shape_type(QPointF(start), QPointF(start), self.pen)

        self.update()
    
    # events
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("white"))
        painter.setPen(QPen(QColor("gray"), 1))

        for x in range(0, self.width(), GRID_SIZE):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), GRID_SIZE):
            painter.drawLine(0, y, self.width(), y)

        for shape in self.shapes:
            painter.setPen(shape.pen)
            shape.draw(painter)

        if self.preview:
            painter.setPen(self.preview.pen)
            self.preview.draw(painter)

        if self.selected:
            self.draw_handles(painter, self.selected)

    def draw_handles(self, painter, shape):
        painter.setPen(QPen(QColor("#f08a24"), 1.5))
        painter.setBrush(QColor("white"))
        half = HANDLE_SIZE / 2
        for h in shape.handles():
            painter.drawRect(QRectF(h.x() - half, h.y() - half, HANDLE_SIZE, HANDLE_SIZE))
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.open_menu(event)
        elif event.button() == Qt.MouseButton.LeftButton:
            if self.preview:
                self.preview.end = event.position()
                self.shapes.append(self.preview)
                self.preview = None
                self.unsetCursor()
            elif self.pending:
                point = QPointF(event.position())
                self.preview = self.pending(point, QPointF(event.position()), self.pen)
                self.pending = None
            else:
                pos = event.position()
                handle = self.selected.handle_at(pos) if self.selected else None
                shape = self.shape_at(pos)

                if handle is not None:
                    self.handle_drag = handle
                    self.setCursor(Qt.CursorShape.SizeAllCursor)
                elif shape:
                    self.set_selected(shape)
                    self.dragging = shape
                    self.drag_last = pos
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                else:
                    self.set_selected(None)
            self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()

        if self.handle_drag is not None:
            self.selected.move_handle(self.handle_drag, pos)
            self.shape_edited.emit()
            self.update()
        elif self.dragging:
            self.dragging.move(pos - self.drag_last)
            self.drag_last = pos
            self.shape_edited.emit()
            self.update()
        elif self.preview:
            self.preview.end = pos
            self.update()
        elif not self.pending:
            if self.selected and self.selected.handle_at(pos) is not None:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            elif self.shape_at(pos):
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.unsetCursor()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.handle_drag is not None:
            self.handle_drag = None
            self.setCursor(Qt.CursorShape.SizeAllCursor)  # still over the handle
        elif event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = None
            self.drag_last = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)  # still over the shape