GRID_SIZE=50
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
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
    def __init__(self):
        super().__init__()
        self.setFixedSize(900,700)
        self.setMouseTracking(True)

        self.preview = None
        self.pending = None # ctrl click initiated state
        
        self.shapes = []
        self.pen = QPen(QColor("black"), 2) # default style

    def open_menu(self, event):
        print(event.button(), event.modifiers())
        start = event.position()
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
            self.preview = None
            self.pending = None
            self.unsetCursor()

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
            self.update()

    def mouseMoveEvent(self, event):
        if self.preview:
            self.preview.end = event.position()
            self.update()