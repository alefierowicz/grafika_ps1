from math import hypot

class Circle:
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def draw(self, painter):
        radius = hypot(self.end.x() - self.start.x(), self.end.y() - self.start.y())
        painter.drawEllipse(self.start, radius, radius)