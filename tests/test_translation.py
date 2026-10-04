"""The Swedish translation loads and covers the panel (skipped without QGIS)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("qgis.core")

from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsVectorLayer  # noqa: E402
from qgis.gui import QgsMapCanvas  # noqa: E402
from qgis.PyQt.QtCore import QCoreApplication, QTranslator  # noqa: E402
from qgis.testing import start_app  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
start_app()

from contour_labeler import output  # noqa: E402
from contour_labeler.dockwidget import ContourLabelerDockWidget  # noqa: E402

QM = Path(__file__).resolve().parent.parent / "contour_labeler" / "i18n" / "contour_labeler_sv.qm"


class FakeIface:
    def __init__(self, canvas):
        self._canvas = canvas

    def mapCanvas(self):
        return self._canvas


@pytest.fixture
def swedish():
    translator = QTranslator()
    assert translator.load(str(QM))
    QCoreApplication.installTranslator(translator)
    yield
    QCoreApplication.removeTranslator(translator)


def test_panel_is_swedish(swedish):
    project = QgsProject.instance()
    project.removeAllMapLayers()
    contours = QgsVectorLayer("LineString?crs=EPSG:3006&field=ELEV:integer", "c", "memory")
    f = QgsFeature(contours.fields())
    f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(-50, 10), QgsPointXY(50, 10)]))
    f["ELEV"] = 100
    contours.dataProvider().addFeature(f)
    project.addMapLayer(contours)
    canvas = QgsMapCanvas()
    canvas.setDestinationCrs(contours.crs())

    dock = ContourLabelerDockWidget(FakeIface(canvas))
    assert dock.windowTitle() == "Höjdkurvsetiketter"
    assert dock.draw_button.text() == "Rita etikettstege"
    assert dock.undo_button.text() == "Ångra senaste stegen"

    dock._on_guide_finished([QgsPointXY(0, 0), QgsPointXY(0, 20)])
    assert dock.status.text() == "Lade till 1 etikett."
    assert output.find_output_layer(project).name() == "Höjdkurvsetiketter"
    dock.undo_last()
    assert dock.status.text() == "Tog bort 1 etikett."
    dock.cleanup()
