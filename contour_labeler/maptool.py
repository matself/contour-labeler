"""Map tool for drawing an uphill guide line."""
from qgis.core import Qgis, QgsGeometry, QgsPointXY
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor


class GuideTool(QgsMapTool):
    """Left-click adds a vertex, right-click/Enter finishes, Backspace removes the last
    vertex, Esc cancels. Emits ``guide_finished(list[QgsPointXY])`` in canvas CRS and stays
    active so the next guide can be drawn straight away."""

    guide_finished = pyqtSignal(list)  # noqa: N815
    undo_requested = pyqtSignal()

    def __init__(self, canvas):
        super().__init__(canvas)
        self.points = []
        self.band = QgsRubberBand(canvas, Qgis.GeometryType.Line)
        self.band.setColor(QColor(220, 30, 30, 200))
        self.band.setWidth(2)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def _redraw(self, cursor=None):
        pts = list(self.points)
        if cursor is not None and pts:
            pts.append(QgsPointXY(cursor))
        if len(pts) < 2:
            self.band.reset(Qgis.GeometryType.Line)
            return
        self.band.setToGeometry(QgsGeometry.fromPolylineXY(pts), None)

    def _clear(self):
        self.points = []
        self.band.reset(Qgis.GeometryType.Line)

    def _finish(self):
        if len(self.points) >= 2:
            points = list(self.points)
            self._clear()
            self.guide_finished.emit(points)
        else:
            self._clear()

    def canvasMoveEvent(self, event):
        self._redraw(event.mapPoint())

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.points.append(QgsPointXY(event.mapPoint()))
            self._redraw()
        elif event.button() == Qt.MouseButton.RightButton:
            self._finish()

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finish()
        elif key == Qt.Key.Key_Escape:
            self._clear()
        elif key == Qt.Key.Key_Backspace and self.points:
            self.points.pop()
            self._redraw()
        elif key == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.undo_requested.emit()
        else:
            return
        event.accept()

    def deactivate(self):
        self._clear()
        super().deactivate()

    def cleanup(self):
        self._clear()
        self.canvas().scene().removeItem(self.band)
