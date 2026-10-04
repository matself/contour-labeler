"""Dock widget for Contour_labeler."""
from qgis.PyQt.QtWidgets import QDockWidget, QLabel, QVBoxLayout, QWidget


class ContourLabelerDockWidget(QDockWidget):
    """Minimal code-only dock widget (no .ui file, so no uic differences Qt5/Qt6)."""

    def __init__(self, parent=None):
        super().__init__("Contour_labeler", parent)
        self.setObjectName("ContourLabelerDockWidget")

        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.addWidget(QLabel("Hello from Contour_labeler!"))
        layout.addStretch()
        self.setWidget(content)
