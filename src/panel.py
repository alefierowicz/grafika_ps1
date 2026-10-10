from PySide6.QtWidgets import QColorDialog, QComboBox, QFormLayout, QPushButton, QSpinBox, QWidget
from PySide6.QtCore import Qt
STYLES = {
    "solid": Qt.PenStyle.SolidLine,
    "dash": Qt.PenStyle.DashLine,
    "dot": Qt.PenStyle.DotLine,
    "dash-dot": Qt.PenStyle.DashDotLine,
}

class StylePanel(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.setFixedWidth(200)

        # TODO: check z prowadzacym bo moze byc bida w spec pisze ze pole tekstowe
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