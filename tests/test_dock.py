"""Dock + output layer + undo, driven without a GUI session."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("qgis.core")

from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsVectorLayer  # noqa: E402
from qgis.gui import QgsMapCanvas  # noqa: E402
from qgis.testing import start_app  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
start_app()

from contour_labeler import output  # noqa: E402
from contour_labeler.dockwidget import ContourLabelerDockWidget  # noqa: E402


class FakeIface:
    def __init__(self, canvas):
        self._canvas = canvas

    def mapCanvas(self):
        return self._canvas


def test_draw_and_undo():
    project = QgsProject.instance()
    project.removeAllMapLayers()
    contours = QgsVectorLayer("LineString?crs=EPSG:3006&field=ELEV:integer", "cont", "memory")
    for i, y in enumerate((10, 20, 30)):
        f = QgsFeature(contours.fields())
        f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(-50, y), QgsPointXY(50, y)]))
        f["ELEV"] = 100 + 5 * i
        contours.dataProvider().addFeature(f)
    project.addMapLayer(contours)

    canvas = QgsMapCanvas()
    canvas.setDestinationCrs(contours.crs())
    dock = ContourLabelerDockWidget(FakeIface(canvas))
    assert dock.field_combo.currentField() == "ELEV"  # guessed
    assert dock.draw_button.isEnabled()

    dock._on_guide_finished([QgsPointXY(0, 0), QgsPointXY(0, 40)])
    out = output.find_output_layer(project)
    assert out.featureCount() == 3
    dock._on_guide_finished([QgsPointXY(20, 0), QgsPointXY(20, 25)])
    assert out.featureCount() == 5
    assert len(project.mapLayersByName(output.LAYER_NAME)) == 1  # reused

    dock.undo_last()
    assert out.featureCount() == 3
    dock.undo_last()
    assert out.featureCount() == 0
    assert not dock.undo_button.isEnabled()
    dock.cleanup()


def test_font_change_updates_output_layer():
    project = QgsProject.instance()
    project.removeAllMapLayers()
    contours = QgsVectorLayer("LineString?crs=EPSG:3006&field=ELEV:integer", "cont", "memory")
    f = QgsFeature(contours.fields())
    f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(-50, 10), QgsPointXY(50, 10)]))
    f["ELEV"] = 100
    contours.dataProvider().addFeature(f)
    project.addMapLayer(contours)
    canvas = QgsMapCanvas()
    canvas.setDestinationCrs(contours.crs())
    dock = ContourLabelerDockWidget(FakeIface(canvas))

    fmt = dock.font_button.textFormat()
    fmt.setSize(14)
    dock.font_button.setTextFormat(fmt)
    dock._on_guide_finished([QgsPointXY(0, 0), QgsPointXY(0, 20)])
    out = output.find_output_layer(project)
    assert out.labeling().settings().format().size() == 14

    fmt.setSize(20)
    dock.font_button.setTextFormat(fmt)
    dock._on_font_changed()
    assert out.labeling().settings().format().size() == 20
    dock.cleanup()


def test_guide_rubber_band_has_geometry():
    from contour_labeler.maptool import GuideTool

    canvas = QgsMapCanvas()
    tool = GuideTool(canvas)
    tool.points = [QgsPointXY(0, 0), QgsPointXY(0, 10)]
    tool._redraw(QgsPointXY(5, 20))
    assert tool.band.asGeometry().length() > 0
    tool.cleanup()
