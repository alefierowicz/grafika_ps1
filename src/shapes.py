from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen
from math import hypot, sqrt

HIT_TOLERANCE = 6
HANDLE_SIZE = 8


def distance_to_segment(p, a, b):
    A = a.y() - b.y()
    B = b.x() - a.x()
    C = a.x() * b.y() - b.x() * a.y()

    if A == 0 and B == 0:
        return hypot(p.x() - a.x(), p.y() - a.y())

    # projecting the point
    if (p.x() - a.x()) * B - (p.y() - a.y()) * A <= 0:
        return hypot(p.x() - a.x(), p.y() - a.y())

    if (p.x() - b.x()) * B - (p.y() - b.y()) * A >= 0:
        return hypot(p.x() - b.x(), p.y() - b.y())

    return abs(A * p.x() + B * p.y() + C) / sqrt(A * A + B * B)

class Shape:
    # names of the text fields that describe this shape, in order
    FIELDS = []

    def __init__(self, start, end, pen):
        self.start = start
        self.end = end
        self.pen = QPen(pen)

    @classmethod
    def from_params(cls, values, pen):
        shape = cls(QPointF(), QPointF(), pen)
        shape.set_params(values)
        return shape

    def params(self):
        raise NotImplementedError

    def set_params(self, values):
        raise NotImplementedError

    def move(self, delta):
        self.start = self.start + delta
        self.end = self.end + delta

    def hit_test(self, point):
        return self.edge_distance(point) <= HIT_TOLERANCE + self.pen.widthF() / 2

    def edge_distance(self, point):
        raise NotImplementedError

    def handles(self):
        raise NotImplementedError

    def move_handle(self, index, pos):
        raise NotImplementedError

    def handle_at(self, point):
        for i, h in enumerate(self.handles()):
            if hypot(point.x() - h.x(), point.y() - h.y()) <= HANDLE_SIZE:
                return i
        return None


class Line(Shape):
    FIELDS = ["x1", "y1", "x2", "y2"]

    def params(self):
        return [self.start.x(), self.start.y(), self.end.x(), self.end.y()]

    def set_params(self, values):
        x1, y1, x2, y2 = values
        self.start = QPointF(x1, y1)
        self.end = QPointF(x2, y2)

    def draw(self, painter):
        painter.drawLine(self.start, self.end)

    def edge_distance(self, point):
        return distance_to_segment(point, self.start, self.end)

    def handles(self):
        return [self.start, self.end]

    def move_handle(self, index, pos):
        # moving one end leaves the other where it is
        if index == 0:
            self.start = QPointF(pos)
        else:
            self.end = QPointF(pos)


class Rectangle(Shape):
    FIELDS = ["x", "y", "width", "height"]

    def params(self):
        r = self.rect()
        return [r.x(), r.y(), r.width(), r.height()]

    def set_params(self, values):
        x, y, w, h = values
        self.start = QPointF(x, y)
        self.end = QPointF(x + w, y + h)

    def rect(self):
        return QRectF(self.start, self.end).normalized()

    def draw(self, painter):
        painter.drawRect(self.rect())

    def edge_distance(self, point):
        r = self.rect()
        corners = [r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft()]
        # distance to the nearest of the four sides
        return min(distance_to_segment(point, corners[i], corners[(i + 1) % 4])
                   for i in range(4))

    def handles(self):
        return [
            self.start,                              # 0
            QPointF(self.end.x(), self.start.y()),   # 1
            self.end,                                # 2
            QPointF(self.start.x(), self.end.y()),   # 3
        ]

    def move_handle(self, index, pos):
        sx, sy, ex, ey = self.start.x(), self.start.y(), self.end.x(), self.end.y()
        if index == 0:
            sx, sy = pos.x(), pos.y()
        elif index == 1:
            ex, sy = pos.x(), pos.y()
        elif index == 2:
            ex, ey = pos.x(), pos.y()
        else:
            sx, ey = pos.x(), pos.y()
        self.start = QPointF(sx, sy)
        self.end = QPointF(ex, ey)


class Circle(Shape):
    FIELDS = ["centre x", "centre y", "radius"]

    def params(self):
        return [self.start.x(), self.start.y(), self.radius()]

    def set_params(self, values):
        cx, cy, r = values
        # start = centre, end = any point on the edge (here: straight to the right)
        self.start = QPointF(cx, cy)
        self.end = QPointF(cx + r, cy)

    def radius(self):
        return hypot(self.end.x() - self.start.x(), self.end.y() - self.start.y())

    def draw(self, painter):
        r = self.radius()
        painter.drawEllipse(self.start, r, r)

    def edge_distance(self, point):
        from_centre = hypot(point.x() - self.start.x(), point.y() - self.start.y())
        return abs(from_centre - self.radius())

    def handles(self):
        # four points on the edge: top, right, bottom, left
        cx, cy, r = self.start.x(), self.start.y(), self.radius()
        return [QPointF(cx, cy - r), QPointF(cx + r, cy),
                QPointF(cx, cy + r), QPointF(cx - r, cy)]

    def move_handle(self, index, pos):
        # any edge handle sets the radius; the centre stays put
        self.end = QPointF(pos)
