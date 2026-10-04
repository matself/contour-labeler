"""The output layer: a memory point layer with elevation and rotation, pre-styled."""
from qgis.core import (
    Qgis,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsProperty,
    QgsTextFormat,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtGui import QColor

from .compat import DOUBLE_FIELD, SHOW_UPSIDE_DOWN_WHEN_ROTATION_DEFINED

LAYER_NAME = "Contour labels"
MARKER_PROPERTY = "contour_labeler/output"
ELEVATION_FIELD = "elev"
ROTATION_FIELD = "rotation"


def find_output_layer(project, crs=None):
    """Existing output layer in the project (matching ``crs`` if given), else None."""
    for layer in project.mapLayers().values():
        if layer.customProperty(MARKER_PROPERTY) and (crs is None or layer.crs() == crs):
            return layer
    return None


def create_output_layer(project, crs):
    layer = QgsVectorLayer(f"Point?crs={crs.authid() or crs.toWkt()}", LAYER_NAME, "memory")
    layer.dataProvider().addAttributes(
        [QgsField(ELEVATION_FIELD, DOUBLE_FIELD), QgsField(ROTATION_FIELD, DOUBLE_FIELD)]
    )
    layer.updateFields()
    layer.setCustomProperty(MARKER_PROPERTY, True)
    _apply_style(layer)
    project.addMapLayer(layer)
    return layer


def add_labels(layer, labels):
    """Add LabelPoints to ``layer``; return the new feature ids (for undo)."""
    features = []
    for label in labels:
        feat = QgsFeature(layer.fields())
        feat.setGeometry(QgsGeometry.fromPointXY(label.point))
        feat.setAttribute(ELEVATION_FIELD, label.elevation)
        feat.setAttribute(ROTATION_FIELD, label.rotation)
        features.append(feat)
    ok, added = layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    layer.triggerRepaint()
    return [f.id() for f in added] if ok else []


def remove_labels(layer, feature_ids):
    layer.dataProvider().deleteFeatures(feature_ids)
    layer.updateExtents()
    layer.triggerRepaint()


def _apply_style(layer):
    settings = QgsPalLayerSettings()
    settings.enabled = True
    settings.fieldName = ELEVATION_FIELD
    settings.placement = Qgis.LabelPlacement.OverPoint
    settings.upsidedownLabels = SHOW_UPSIDE_DOWN_WHEN_ROTATION_DEFINED

    fmt = QgsTextFormat()
    fmt.setColor(QColor("black"))
    fmt.setSize(9)
    settings.setFormat(fmt)

    props = settings.dataDefinedProperties()
    props.setProperty(QgsPalLayerSettings.Property.LabelRotation,
                      QgsProperty.fromField(ROTATION_FIELD))
    settings.setDataDefinedProperties(props)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.setLabelsEnabled(True)

    # White collar that knocks out the contour behind the label.
    symbol = QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": "white", "size": "5", "outline_style": "no"}
    )
    layer.renderer().setSymbol(symbol)
