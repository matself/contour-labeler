"""Small shims so the same code runs on QGIS 3 (Qt5) and QGIS 4 (Qt6).

Rules of thumb for the rest of the plugin:
  * import Qt only through ``qgis.PyQt`` (never ``PyQt5`` / ``PyQt6``)
  * use fully scoped enums, e.g. ``Qt.DockWidgetArea.RightDockWidgetArea``
  * call ``exec()``, not ``exec_()``
  * ``from qgis.PyQt import sip`` instead of a bare ``import sip``
Anything that cannot be written in a way that works on both goes in this module.
"""
from qgis.core import Qgis, QgsPalLayerSettings
from qgis.PyQt.QtCore import QT_VERSION_STR

try:  # Qt6: QAction lives in QtGui
    from qgis.PyQt.QtGui import QAction
except ImportError:  # Qt5: QAction lives in QtWidgets
    from qgis.PyQt.QtWidgets import QAction

# Field type constant for QgsField: QVariant on Qt5, QMetaType on Qt6.
if int(QT_VERSION_STR.split(".")[0]) >= 6:
    from qgis.PyQt.QtCore import QMetaType

    DOUBLE_FIELD = QMetaType.Type.Double
else:
    from qgis.PyQt.QtCore import QVariant

    DOUBLE_FIELD = QVariant.Double

try:  # QGIS >= 3.32
    SHOW_UPSIDE_DOWN_WHEN_ROTATION_DEFINED = (
        Qgis.UpsideDownLabelHandling.AllowUpsideDownWhenRotationIsDefined
    )
except AttributeError:
    SHOW_UPSIDE_DOWN_WHEN_ROTATION_DEFINED = QgsPalLayerSettings.ShowDefined

__all__ = ["QAction", "DOUBLE_FIELD", "SHOW_UPSIDE_DOWN_WHEN_ROTATION_DEFINED"]
