import sys
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QColorDialog, QComboBox, QFormLayout, QHBoxLayout, QPushButton, QSpinBox, QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QMenu

from shapes import *

GRID_SIZE=50
STYLES = {
    "solid": Qt.PenStyle.SolidLine,
    "dash": Qt.PenStyle.DashLine,
    "dot": Qt.PenStyle.DotLine,
    "dash-dot": Qt.PenStyle.DashDotLine,
}

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
            
class StylePanel(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.setFixedWidth(200)

        self.width_box = QSpinBox()
        self.width_box.setRange(1,20)
        self.width_box.setValue(canvas.pen.width())
        self.width_box.valueChanged.connect(self.set_width)

        self.color_button = QPushButton()
        self.color_button.clicked.connect(self.pick_color)
        self.show_color(canvas.pen.color())

        self.style_box = QComboBox()
        self.style_box.addItems(list(STYLES))
        self.style_box.currentTextChanged.connect(self.set_style)

        form = QFormLayout(self)
        form.addRow("thickness", self.width_box)
        form.addRow("color", self.color_button)
        form.addRow("line style", self.style_box)

    def set_width(self, value):
        self.canvas.pen.setWidth(value)

    def set_style(self, name):
        self.canvas.pen.setStyle(STYLES[name])

    def pick_color(self):
        color = QColorDialog.getColor(self.canvas.pen.color(), self)
        if color.isValid():
            self.canvas.pen.setColor(color)
            self.show_color(color)
    def show_color(self, color):
        self.color_button.setStyleSheet(f"background-color: {color.name()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    canvas = Canvas()
    panel = StylePanel(canvas)

    window = QWidget()
    layout = QHBoxLayout(window)
    layout.addWidget(canvas)
    layout.addWidget(panel, alignment=Qt.AlignmentFlag.AlignTop)

    window.show()
    sys.exit(app.exec())