"""Ladder logic against real geometries (skipped when QGIS is not importable)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("qgis.core")

from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer  # noqa: E402
from qgis.testing import start_app  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
start_app()

from contour_labeler import core  # noqa: E402


def make_contours(*lines):
    layer = QgsVectorLayer("LineString?crs=EPSG:3006&field=elev:double", "c", "memory")
    for elev, pts in lines:
        f = QgsFeature(layer.fields())
        f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(*p) for p in pts]))
        f["elev"] = elev
        layer.dataProvider().addFeature(f)
    return layer


def ladder(layer, guide):
    return core.compute_ladder(layer, "elev", [QgsPointXY(*p) for p in guide], 5.0)


def test_rotation_independent_of_contour_direction():
    # Horizontal contours at y=10 and y=20; guide goes north (uphill).
    fwd = make_contours((100, [(-50, 10), (50, 10)]), (105, [(-50, 20), (50, 20)]))
    rev = make_contours((100, [(50, 10), (-50, 10)]), (105, [(50, 20), (-50, 20)]))
    a = sorted(ladder(fwd, [(0, 0), (0, 30)]), key=lambda x: x.elevation)
    b = sorted(ladder(rev, [(0, 0), (0, 30)]), key=lambda x: x.elevation)
    assert [x.elevation for x in a] == [100, 105]
    for x, y in zip(a, b):
        assert x.rotation == pytest.approx(y.rotation)
    assert a[0].rotation == pytest.approx(0)  # text top points north = uphill


def test_flipping_guide_flips_label():
    c = make_contours((100, [(-50, 10), (50, 10)]))
    up = ladder(c, [(0, 0), (0, 30)])[0].rotation
    down = ladder(c, [(0, 30), (0, 0)])[0].rotation
    assert abs(up - down) == pytest.approx(180)


def test_vertex_crossing_not_duplicated():
    c = make_contours((100, [(-50, 10), (50, 10)]))
    assert len(ladder(c, [(0, 0), (0, 10), (0, 30)])) == 1


def test_missing_elevation_skipped():
    c = make_contours((None, [(-50, 10), (50, 10)]))
    assert ladder(c, [(0, 0), (0, 30)]) == []


def test_bent_guide_uses_local_segment():
    c = make_contours((100, [(-50, 10), (50, 10)]), (105, [(10, -50), (10, 50)]))
    res = {r.elevation: r.rotation for r in ladder(c, [(0, 0), (0, 15), (30, 15)])}
    assert res[100] == pytest.approx(0)    # crossed heading north
    assert res[105] == pytest.approx(90)   # crossed heading east
