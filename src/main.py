import sys
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget
from PySide6.QtCore import Qt

from canvas import *
from panel import *

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