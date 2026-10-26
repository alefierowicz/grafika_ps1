import csv

from PySide6.QtGui import QPen
from PySide6.QtWidgets import (QComboBox, QFileDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget)

from shapes import Circle, Line, Rectangle

SHAPE_TYPES = {
    "line": Line,
    "rectangle": Rectangle,
    "circle": Circle,
}
TYPE_NAMES = {cls: name for name, cls in SHAPE_TYPES.items()}


def fmt(value):
    return f"{round(value, 2):g}"


class ParamPanel(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.shape = None  # the selected shape being edited, or None = "add" mode
        self.setFixedWidth(220)

        # tells you which mode the panel is in
        self.title = QLabel()
        self.title.setStyleSheet("font-weight: bold")

        # which shape to create
        self.type_box = QComboBox()
        self.type_box.addItems(list(SHAPE_TYPES))
        self.type_box.currentTextChanged.connect(self.rebuild_fields)

        self.form = QFormLayout()
        self.inputs = []

        self.width_input = QLineEdit(str(canvas.pen.width()))
        self.form.addRow("line width", self.width_input)

        # "add" or "apply", depending on the mode
        self.button = QPushButton()
        self.button.clicked.connect(self.submit)

        # feedback for invalid input
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #c0392b")
        self.error_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.type_box)
        layout.addLayout(self.form)
        layout.addWidget(self.button)
        layout.addWidget(self.error_label)
        layout.addStretch()

        # saving / loading the whole drawing, pinned to the bottom-right
        load_button = QPushButton("load")
        load_button.clicked.connect(self.load)
        export_button = QPushButton("export")
        export_button.clicked.connect(self.export)

        file_row = QHBoxLayout()
        file_row.addStretch()
        file_row.addWidget(load_button)
        file_row.addWidget(export_button)
        layout.addLayout(file_row)

        self.rebuild_fields(self.type_box.currentText())
        self.show_shape(None)

        # keep the panel in sync with what happens on the canvas
        canvas.selection_changed.connect(self.show_shape)
        canvas.shape_edited.connect(self.refresh)

    def show_shape(self, shape):
        self.shape = shape
        self.error_label.clear()

        if shape is None:
            self.title.setText("new shape")
            self.type_box.setEnabled(True)
            self.button.setText("add")
            return

        self.title.setText("selected shape")
        # switching the type rebuilds the fields if it differs from the current one
        self.type_box.setCurrentText(TYPE_NAMES[type(shape)])
        self.type_box.setEnabled(False)  # an existing shape can't change its type
        self.button.setText("apply")
        self.refresh()

    def refresh(self):
        """Fill the fields with the selected shape's current values."""
        if self.shape is None:
            return
        for field, value in zip(self.inputs, self.shape.params()):
            field.setText(fmt(value))
        self.width_input.setText(fmt(self.shape.pen.widthF()))

    def rebuild_fields(self, type_name):
        for _ in self.inputs:
            self.form.removeRow(0)
        self.inputs = []

        for i, name in enumerate(SHAPE_TYPES[type_name].FIELDS):
            field = QLineEdit()
            self.form.insertRow(i, name, field)
            self.inputs.append(field)

        self.error_label.clear()

    def read_inputs(self):
        try:
            values = [float(field.text()) for field in self.inputs]
            width = float(self.width_input.text())
        except ValueError:
            self.error_label.setText("all fields must be numbers")
            return None

        if width <= 0:
            self.error_label.setText("line width must be greater than 0")
            return None

        self.error_label.clear()
        return values, width

    def submit(self):
        parsed = self.read_inputs()
        if parsed is None:
            return
        values, width = parsed

        if self.shape is None:
            # add mode: 
            pen = QPen(self.canvas.pen)
            pen.setWidthF(width)
            shape_type = SHAPE_TYPES[self.type_box.currentText()]
            self.canvas.shapes.append(shape_type.from_params(values, pen))
        else:
            # edit mode: 
            self.shape.set_params(values)
            self.shape.pen.setWidthF(width)
            self.refresh()  # show the values the way the shape stores them

        self.canvas.update()

    # one shape per row: type, line width, then its params 
    # for instance: circle,2,450,350,100

    def export(self):
        path, _ = QFileDialog.getSaveFileName(self, "export drawing", "drawing.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            for shape in self.canvas.shapes:
                writer.writerow([TYPE_NAMES[type(shape)], shape.pen.widthF(), *shape.params()])

    def load(self):
        path, _ = QFileDialog.getOpenFileName(self, "load drawing", "", "CSV (*.csv)")
        if not path:
            return
        shapes = []
        try:
            with open(path, newline="") as f:
                for row in csv.reader(f):
                    if not row:
                        continue
                    shape_type = SHAPE_TYPES[row[0]]
                    width, *values = map(float, row[1:])
                    if len(values) != len(shape_type.FIELDS):
                        raise ValueError
                    pen = QPen(self.canvas.pen)
                    pen.setWidthF(width)
                    shapes.append(shape_type.from_params(values, pen))
        except (OSError, KeyError, ValueError):
            self.error_label.setText("couldn't read that file")
            return

        # only replace the drawing once the whole file parsed fine
        self.error_label.clear()
        self.canvas.shapes = shapes
        self.canvas.set_selected(None)
        self.canvas.update()
