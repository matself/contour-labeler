"""Dock panel: pick contours, draw guides, undo."""
from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsProject,
    QgsUnitTypes,
)
from qgis.gui import QgsCollapsibleGroupBox, QgsFieldComboBox, QgsMapLayerComboBox
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import core, output
from .maptool import GuideTool


def _tr(message, disambiguation=None, n=-1):
    return QCoreApplication.translate("ContourLabelerDockWidget", message, disambiguation, n)


SCOPE = "contour_labeler"
LIKELY_ELEVATION_FIELDS = ("elev", "ele", "z", "height", "hojd", "höjd", "altitude", "value")


class ContourLabelerDockWidget(QDockWidget):
    """Code-only dock widget (no .ui file, so no uic differences between Qt5/Qt6)."""

    def __init__(self, iface, parent=None):
        super().__init__(_tr("Contour Labeler"), parent)
        self.setObjectName("ContourLabelerDockWidget")
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.undo_stack = []  # one entry per guide: (layer id, [feature ids])
        self.tool = GuideTool(self.canvas)
        self.tool.guide_finished.connect(self._on_guide_finished)
        self.tool.undo_requested.connect(self.undo_last)
        self.tool.deactivated.connect(lambda: self.draw_button.setChecked(False))

        content = QWidget(self)
        layout = QVBoxLayout(content)

        # --- Contours -------------------------------------------------------
        form = QFormLayout()
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(Qgis.LayerFilter.LineLayer)
        self.field_combo = QgsFieldComboBox()
        try:
            from qgis.core import QgsFieldProxyModel
            self.field_combo.setFilters(QgsFieldProxyModel.Filter.Numeric)
        except AttributeError:
            from qgis.core import QgsFieldProxyModel
            self.field_combo.setFilters(QgsFieldProxyModel.Numeric)
        form.addRow(_tr("Contour layer"), self.layer_combo)
        form.addRow(_tr("Elevation field"), self.field_combo)
        layout.addLayout(form)

        # --- Drawing --------------------------------------------------------
        self.draw_button = QPushButton(_tr("Draw label ladder"))
        self.draw_button.setCheckable(True)
        self.draw_button.setMinimumHeight(36)
        layout.addWidget(self.draw_button)

        self.hint = QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

        undo_row = QHBoxLayout()
        self.undo_button = QPushButton(_tr("Undo last ladder"))
        self.undo_button.setToolTip(_tr("Remove the labels from the last guide (Ctrl+Z)"))
        self.save_button = QPushButton(_tr("Save output…"))
        self.save_button.setToolTip(
            _tr("The output is a temporary layer. Save it to keep the labels.")
        )
        undo_row.addWidget(self.undo_button)
        undo_row.addWidget(self.save_button)
        layout.addLayout(undo_row)

        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        # --- Options --------------------------------------------------------
        options = QgsCollapsibleGroupBox(_tr("Options"))
        options.setCollapsed(True)
        opt_form = QFormLayout(options)
        self.tangent_spin = QDoubleSpinBox()
        self.tangent_spin.setRange(0.1, 1000)
        self.tangent_spin.setValue(core.DEFAULT_TANGENT_M)
        self.tangent_spin.setSuffix(" m")
        self.tangent_spin.setToolTip(
            _tr("Distance each side of the crossing used to find the contour direction. "
                    "Increase for jagged contours.")
        )
        opt_form.addRow(_tr("Smoothing distance"), self.tangent_spin)
        layout.addWidget(options)

        layout.addStretch()
        self.setWidget(content)

        self.layer_combo.layerChanged.connect(self._on_layer_changed)
        self.field_combo.fieldChanged.connect(self._on_field_changed)
        self.draw_button.toggled.connect(self._on_draw_toggled)
        self.undo_button.clicked.connect(self.undo_last)
        self.save_button.clicked.connect(self._save_output)
        QgsProject.instance().layersWillBeRemoved.connect(self._on_layers_removed)

        self._restore_from_project()
        self._on_layer_changed(self.layer_combo.currentLayer())
        self._update_state()

    # --- state ---------------------------------------------------------------
    def _restore_from_project(self):
        project = QgsProject.instance()
        layer_id, _ = project.readEntry(SCOPE, "contour_layer", "")
        layer = project.mapLayer(layer_id) if layer_id else None
        if layer is not None:
            self.layer_combo.setLayer(layer)

    def _on_layer_changed(self, layer):
        self.field_combo.setLayer(layer)
        if layer is None:
            return
        QgsProject.instance().writeEntry(SCOPE, "contour_layer", layer.id())
        saved, _ = QgsProject.instance().readEntry(SCOPE, f"field/{layer.id()}", "")
        names = [f.name() for f in layer.fields()]
        guess = next((n for n in names if n.lower() in LIKELY_ELEVATION_FIELDS), "")
        for candidate in (saved, guess):
            if candidate in names:
                self.field_combo.setField(candidate)
                break
        self._update_state()

    def _on_field_changed(self, field):
        layer = self.layer_combo.currentLayer()
        if layer is not None and field:
            QgsProject.instance().writeEntry(SCOPE, f"field/{layer.id()}", field)
        self._update_state()

    def _on_layers_removed(self, layer_ids):
        self.undo_stack = [e for e in self.undo_stack if e[0] not in layer_ids]
        self._update_state()

    def _ready(self):
        return self.layer_combo.currentLayer() is not None and bool(self.field_combo.currentField())

    def _update_state(self):
        ready = self._ready()
        self.draw_button.setEnabled(ready)
        self.undo_button.setEnabled(bool(self.undo_stack))
        self.save_button.setEnabled(output.find_output_layer(QgsProject.instance()) is not None)
        if not ready:
            self.hint.setText(_tr("Choose a contour layer and its elevation field."))
        elif self.draw_button.isChecked():
            self.hint.setText(_tr(
                "Click uphill across the contours. Right-click or Enter finishes, "
                "Backspace removes the last point, Esc cancels."
            ))
        else:
            self.hint.setText(_tr("Draw a guide line uphill; labels are placed where it "
                                      "crosses the contours."))

    # --- drawing -------------------------------------------------------------
    def _on_draw_toggled(self, checked):
        if checked:
            self.canvas.setMapTool(self.tool)
        elif self.canvas.mapTool() is self.tool:
            self.canvas.unsetMapTool(self.tool)
        self._update_state()

    def _tangent_radius(self, layer):
        """Smoothing distance converted from metres to the layer's CRS units."""
        factor = QgsUnitTypes.fromUnitToUnitFactor(
            layer.crs().mapUnits(), Qgis.DistanceUnit.Meters
        )
        return self.tangent_spin.value() / factor if factor else self.tangent_spin.value()

    def _on_guide_finished(self, canvas_points):
        layer = self.layer_combo.currentLayer()
        field = self.field_combo.currentField()
        if layer is None or not field:
            return
        project = QgsProject.instance()
        to_layer = QgsCoordinateTransform(
            self.canvas.mapSettings().destinationCrs(), layer.crs(), project
        )
        points = [to_layer.transform(p) for p in canvas_points]
        labels = core.compute_ladder(layer, field, points, self._tangent_radius(layer))
        if not labels:
            self.status.setText(_tr("No labels: the guide did not cross any contour "
                                        "with an elevation value."))
            return

        out = output.find_output_layer(project, layer.crs()) or output.create_output_layer(
            project, layer.crs()
        )
        ids = output.add_labels(out, labels)
        self.undo_stack.append((out.id(), ids))
        self.status.setText(_tr("Added %n label(s).", None, len(ids)))
        self._update_state()

    def undo_last(self):
        project = QgsProject.instance()
        while self.undo_stack:
            layer_id, ids = self.undo_stack.pop()
            layer = project.mapLayer(layer_id)
            if layer is not None:
                output.remove_labels(layer, ids)
                self.status.setText(_tr("Removed %n label(s).", None, len(ids)))
                break
        self._update_state()

    def _save_output(self):
        layer = output.find_output_layer(QgsProject.instance())
        if layer is not None:
            self.iface.setActiveLayer(layer)
            self.iface.actionLayerSaveAs().trigger()

    # --- lifecycle -----------------------------------------------------------
    def cleanup(self):
        try:
            QgsProject.instance().layersWillBeRemoved.disconnect(self._on_layers_removed)
        except (TypeError, RuntimeError):
            pass
        if self.canvas.mapTool() is self.tool:
            self.canvas.unsetMapTool(self.tool)
        self.tool.cleanup()
