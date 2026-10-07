class Line:
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def draw(self, painter):
        painter.drawLine(self.start, self.end)