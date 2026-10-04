"""Label ladder geometry: where labels go and how they are rotated.

No GUI code here, so it can be tested and reused from scripts.

A *ladder* is a guide polyline drawn uphill. Every place where it crosses a contour
gets a label point. The label's "top" points uphill (along the guide) and its baseline
follows the local tangent of the contour.
"""
import math
from dataclasses import dataclass

from qgis.core import Qgis, QgsFeatureRequest, QgsGeometry, QgsPointXY, QgsWkbTypes

DEFAULT_TANGENT_M = 5.0


@dataclass
class LabelPoint:
    point: QgsPointXY
    elevation: float
    rotation: float  # QGIS convention: degrees clockwise from east, 0-360


def contour_tangent(contour_geom, point, radius):
    """Direction (dx, dy) of the contour around ``point``, averaged over ``radius``.

    The contour is clipped with a circle and the chord of the longest remaining part is
    used, which smooths out digitising noise. Returns None if no direction can be found.
    """
    clipped = contour_geom.intersection(QgsGeometry.fromPointXY(point).buffer(radius, 8))
    if clipped.isEmpty():
        return None
    if clipped.isMultipart():
        parts = clipped.asMultiPolyline()
        pts = max(parts, key=lambda p: QgsGeometry.fromPolylineXY(p).length()) if parts else []
    else:
        pts = clipped.asPolyline()
    if len(pts) < 2:
        return None
    dx, dy = pts[-1].x() - pts[0].x(), pts[-1].y() - pts[0].y()
    if dx == 0 and dy == 0:
        return None
    return dx, dy


def label_rotation(tangent, uphill):
    """QGIS rotation (clockwise degrees) putting the text top on the uphill side.

    Independent of the digitising direction of the contour: the sign of the dot product
    between the contour normal and the guide direction decides whether to flip 180 deg.
    """
    cx, cy = tangent
    gx, gy = uphill
    angle = math.degrees(math.atan2(cy, cx))  # counter-clockwise from east
    if (-cy * gx + cx * gy) < 0:  # normal points downhill
        angle += 180
    return (-angle) % 360


def _crossing_points(segment_geom, contour_geom):
    inter = segment_geom.intersection(contour_geom)
    if inter.isEmpty() or QgsWkbTypes.geometryType(inter.wkbType()) != Qgis.GeometryType.Point:
        return []  # no crossing, or the guide runs along the contour
    return [QgsPointXY(v.x(), v.y()) for v in inter.vertices()]


def compute_ladder(contour_layer, elevation_field, guide_points, tangent_radius):
    """Return a list of LabelPoint for a guide drawn in the contour layer's CRS.

    ``tangent_radius`` is in the layer's CRS units. Contours without an elevation value
    are skipped. A crossing exactly on a guide vertex is reported once.
    """
    if len(guide_points) < 2:
        return []
    guide = QgsGeometry.fromPolylineXY(guide_points)
    request = QgsFeatureRequest().setFilterRect(guide.boundingBox())
    tolerance = tangent_radius * 0.01
    results = []

    for feature in contour_layer.getFeatures(request):
        value = feature[elevation_field]
        geom = feature.geometry()
        if geom.isNull() or value is None or not guide.intersects(geom):
            continue
        try:
            elevation = float(value)
        except (TypeError, ValueError):
            continue

        found = []  # points already placed on this contour
        for a, b in zip(guide_points, guide_points[1:]):
            if a == b:
                continue
            uphill = (b.x() - a.x(), b.y() - a.y())
            for pt in _crossing_points(QgsGeometry.fromPolylineXY([a, b]), geom):
                if any(pt.distance(p) < tolerance for p in found):
                    continue
                tangent = contour_tangent(geom, pt, tangent_radius)
                if tangent is None:
                    continue
                found.append(pt)
                results.append(LabelPoint(pt, elevation, label_rotation(tangent, uphill)))

    return results
