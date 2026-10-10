GRID_SIZE=50
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QMenu

from shapes import *

class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(900,700)
        self.setMouseTracking(True)
        self.shapes = []
        self.preview = None
        self.pen = QPen(QColor("black"), 2) # default style

    def open_menu(self, event):
            start = event.position()
            menu = QMenu(self)
            
            line_action = menu.addAction("line")
            rect_action = menu.addAction("rectangle")
            circle_action = menu.addAction("circle")
            
            menu.addSeparator()
            clear_action = menu.addAction("clear all")
            
            chosen = menu.exec(event.globalPosition().toPoint())
            if chosen == line_action:
                self.preview = Line(QPointF(start), QPointF(start), self.pen)
            elif chosen == rect_action:
                self.preview = Rectangle(QPointF(start), QPointF(start),self.pen)
            elif chosen == circle_action:
                self.preview = Circle(QPointF(start), QPointF(start),self.pen)
            elif chosen == clear_action:
                self.shapes.clear()
                self.preview = None
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
        elif event.button() == Qt.MouseButton.LeftButton and self.preview:
            self.preview.end = event.position()
            self.shapes.append(self.preview)
            self.preview = None
            self.update()

    def mouseMoveEvent(self, event):
        if self.preview:
            self.preview.end = event.position()
            self.update()