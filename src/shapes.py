from PySide6.QtCore import QRectF
from PySide6.QtGui import QPen
from math import hypot
class Shape:
    def __init__(self, start, end, pen):
        self.start = start
        self.end = end
        self.pen = QPen(pen)


class Line(Shape):
    def draw(self, painter):
        painter.drawLine(self.start, self.end)


class Rectangle(Shape):
    def draw(self, painter):
        painter.drawRect(QRectF(self.start, self.end).normalized())


class Circle(Shape):
    def draw(self, painter):
        radius = hypot(self.end.x() - self.start.x(), self.end.y() - self.start.y())
        painter.drawEllipse(self.start, radius, radius)