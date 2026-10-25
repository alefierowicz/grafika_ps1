from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen
from math import hypot

# how close (in pixels) the cursor must be to an edge to "grab" it
HIT_TOLERANCE = 6
# size of the square handles drawn on a selected shape's characteristic points
HANDLE_SIZE = 8


def distance_to_segment(p, a, b):
    """Shortest distance from point p to the segment a-b."""
    abx, aby = b.x() - a.x(), b.y() - a.y()
    length_sq = abx * abx + aby * aby
    if length_sq == 0:  # segment is a single point
        return hypot(p.x() - a.x(), p.y() - a.y())
    # projection of p onto the segment, clamped to its ends (0 = a, 1 = b)
    t = ((p.x() - a.x()) * abx + (p.y() - a.y()) * aby) / length_sq
    t = max(0.0, min(1.0, t))
    closest_x, closest_y = a.x() + t * abx, a.y() + t * aby
    return hypot(p.x() - closest_x, p.y() - closest_y)


class Shape:
    # names of the text fields that describe this shape, in order
    FIELDS = []

    def __init__(self, start, end, pen):
        self.start = start
        self.end = end
        self.pen = QPen(pen)

    @classmethod
    def from_params(cls, values, pen):
        """Build the shape from numbers typed into the panel (same order as FIELDS)."""
        shape = cls(QPointF(), QPointF(), pen)
        shape.set_params(values)
        return shape

    def params(self):
        """The shape's current numbers, in the same order as FIELDS."""
        raise NotImplementedError

    def set_params(self, values):
        """Reshape this shape from numbers in the same order as FIELDS."""
        raise NotImplementedError

    def move(self, delta):
        """Shift the whole shape by delta (a QPointF)."""
        self.start = self.start + delta
        self.end = self.end + delta

    def hit_test(self, point):
        """True if point is on (close enough to) the shape's outline."""
        return self.edge_distance(point) <= HIT_TOLERANCE + self.pen.widthF() / 2

    def edge_distance(self, point):
        raise NotImplementedError

    def handles(self):
        """Characteristic points that can be dragged to reshape the shape."""
        raise NotImplementedError

    def move_handle(self, index, pos):
        """Put handle number `index` at pos, reshaping the shape around it."""
        raise NotImplementedError

    def handle_at(self, point):
        """Index of the handle under point, or None."""
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
        # normalized, so a rectangle drawn "backwards" still reports
        # its top-left corner and a positive width/height
        r = self.rect()
        return [r.x(), r.y(), r.width(), r.height()]

    def set_params(self, values):
        x, y, w, h = values
        # start = top-left corner, end = opposite corner
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
        # built from start/end directly (not the normalized rect), so each handle
        # stays tied to the same coordinates even if the rectangle gets flipped
        return [
            self.start,                              # 0
            QPointF(self.end.x(), self.start.y()),   # 1
            self.end,                                # 2
            QPointF(self.start.x(), self.end.y()),   # 3
        ]

    def move_handle(self, index, pos):
        # each corner owns one x and one y; the opposite corner never changes
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
