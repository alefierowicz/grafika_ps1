from PySide6.QtCore import QRectF
class Rectangle:
    def __init__(self, start, end):
        self.start = start # top left corner
        self.end = end # bottom right
    def draw(self, painter):
        painter.drawRect(QRectF(self.start, self.end).normalized())
