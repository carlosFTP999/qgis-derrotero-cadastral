"""Dock widget for the Derrotero Catastral plugin.

Provides the main user interface: layer and feature selection, template
choice, generation trigger, preview, and TXT export.
"""

import os
from typing import Any

from qgis.core import QgsProject, QgsVectorLayer
from qgis.gui import QgisInterface, QgsMapLayerComboBox, QgsMapLayerProxyModel
from qgis.PyQt.QtCore import QSettings, QStandardPaths, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from derrotero_catastral.gui.preview import DerroteroPreview
from derrotero_catastral.processing.pipeline import PipelineOrchestrator

# ---------------------------------------------------------------------------
# Settings constants
# ---------------------------------------------------------------------------

_ORG = "derrotero_catastral"
_APP = "derrotero_catastral"
_KEY_LAST_LAYER = "dock/last_layer_id"
_KEY_LAST_COL_LAYER = "dock/last_col_layer_id"
_KEY_LAST_TEMPLATE = "dock/last_template"
_KEY_GEOMETRY = "dock/geometry"
_KEY_STATE = "dock/state"


class DerroteroDock(QDockWidget):
    """Main dock widget for derrotero generation.

    Provides polygon layer selection, feature picker, colindancia layer
    (optional), template selection, a generate button, a text preview
    area, and a TXT export button.
    """

    def __init__(self, iface: QgisInterface, parent=None) -> None:
        super().__init__("Derrotero Catastral", parent)
        self.iface = iface
        self.pipeline = PipelineOrchestrator(iface)

        self.setObjectName("derroteroCatastralDock")
        self.setAllowedAreas(
            Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea
            | Qt.BottomDockWidgetArea
        )

        self._setup_ui()
        self._connect_signals()
        self._restore_settings()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the dock widget layout."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)

        # --- Selection form ---
        form = QFormLayout()

        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.layer_combo.setAllowEmptyLayer(True)
        form.addRow("Capa polígonos:", self.layer_combo)

        self.feature_combo = QComboBox()
        self.feature_combo.setMinimumWidth(200)
        self.feature_combo.setEnabled(False)
        form.addRow("Predio:", self.feature_combo)

        self.colindancia_combo = QgsMapLayerComboBox()
        self.colindancia_combo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.colindancia_combo.setAllowEmptyLayer(True)
        self.colindancia_combo.setLayer(None)
        form.addRow("Colindancias (opcional):", self.colindancia_combo)

        self.template_combo = QComboBox()
        self._populate_template_combo()
        form.addRow("Plantilla:", self.template_combo)

        layout.addLayout(form)

        # --- Generate button ---
        self.generate_btn = QPushButton("Generar Derrotero")
        self.generate_btn.setIcon(
            QIcon.fromTheme("document-new", QIcon())
        )
        layout.addWidget(self.generate_btn)

        # --- Preview ---
        preview_label = QLabel("Vista previa:")
        layout.addWidget(preview_label)

        self.preview = DerroteroPreview()
        layout.addWidget(self.preview, stretch=1)

        # --- Export button ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.export_btn = QPushButton("Exportar TXT")
        self.export_btn.setIcon(
            QIcon.fromTheme("document-save", QIcon())
        )
        self.export_btn.setEnabled(False)
        btn_row.addWidget(self.export_btn)

        layout.addLayout(btn_row)

        self.setWidget(container)

    def _populate_template_combo(self) -> None:
        """Populate the template combo with available ``.j2`` files.

        Scans the built-in blueprints directory and the user templates
        directory.  Built-in templates are listed first, followed by
        user-provided ones.
        """
        self.template_combo.clear()

        # Built-in templates
        plugin_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        builtin_dir = os.path.join(plugin_dir, "template", "blueprints")

        templates: list[str] = []
        if os.path.isdir(builtin_dir):
            for f in sorted(os.listdir(builtin_dir)):
                if f.endswith(".j2") and f not in templates:
                    templates.append(f)

        # User templates (override / additional)
        user_dir = os.path.join(
            QStandardPaths.writableLocation(
                QStandardPaths.AppLocalDataLocation
            ),
            "derrotero",
            "templates",
        )
        if os.path.isdir(user_dir):
            for f in sorted(os.listdir(user_dir)):
                if f.endswith(".j2") and f not in templates:
                    templates.append(f)

        for t in templates:
            self.template_combo.addItem(t)

        # Select default (es.j2 if available, else first)
        index = self.template_combo.findText("es.j2")
        if index >= 0:
            self.template_combo.setCurrentIndex(index)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        """Connect all UI signals to their handlers."""
        self.layer_combo.layerChanged.connect(self._on_layer_changed)
        self.feature_combo.currentIndexChanged.connect(self._on_feature_changed)
        self.generate_btn.clicked.connect(self._on_generate)
        self.export_btn.clicked.connect(self._on_export_txt)

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_layer_changed(self) -> None:
        """Update the feature combo when the polygon layer changes."""
        self.feature_combo.clear()
        self.feature_combo.setEnabled(False)
        self.preview.clear_text()
        self.export_btn.setEnabled(False)

        layer: QgsVectorLayer | None = self.layer_combo.currentLayer()
        if layer is None:
            return

        # Populate feature combo with all feature IDs
        for feat in layer.getFeatures():
            fid = feat.id()
            label = self._feature_label(feat, fid, layer)
            self.feature_combo.addItem(label, fid)

        self.feature_combo.setEnabled(self.feature_combo.count() > 0)

    def _on_feature_changed(self) -> None:
        """Clear the preview when the selected feature changes."""
        self.preview.clear_text()
        self.export_btn.setEnabled(False)

    def _on_generate(self) -> None:
        """Run the pipeline and display the result in the preview."""
        layer: QgsVectorLayer | None = self.layer_combo.currentLayer()
        if layer is None:
            QMessageBox.warning(
                self, "Derrotero Catastral",
                "Seleccione una capa de polígonos."
            )
            return

        feature_id: Any | None = self.feature_combo.currentData()
        if feature_id is None:
            QMessageBox.warning(
                self, "Derrotero Catastral",
                "Seleccione un predio de la capa activa."
            )
            return

        col_layer: QgsVectorLayer | None = (
            self.colindancia_combo.currentLayer()
        )
        template_name: str = self.template_combo.currentText()

        if not template_name:
            QMessageBox.warning(
                self, "Derrotero Catastral",
                "Seleccione una plantilla."
            )
            return

        try:
            result = self.pipeline.run(
                layer=layer,
                feature_id=feature_id,
                colindancia_layer=col_layer,
                template_name=template_name,
            )
            self.preview.set_text(result)
            self.export_btn.setEnabled(bool(result.strip()))
            self._save_settings()

        except ValueError as exc:
            QMessageBox.warning(self, "Derrotero Catastral", str(exc))
        except RuntimeError as exc:
            QMessageBox.critical(self, "Error de renderizado", str(exc))

    def _on_export_txt(self) -> None:
        """Save the current preview content to a TXT file."""
        text = self.preview.get_text()
        if not text.strip():
            QMessageBox.warning(
                self, "Exportar",
                "No hay contenido para exportar. "
                "Genere un derrotero primero."
            )
            return

        # Build a default filename from the current feature
        feature_id: Any | None = self.feature_combo.currentData()
        if feature_id is not None:
            default_name = f"parcel-{feature_id}_derrotero.txt"
        else:
            default_name = "derrotero.txt"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Derrotero",
            default_name,
            "Archivos de texto (*.txt);;Todos los archivos (*)",
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as exc:
            QMessageBox.critical(
                self, "Error al exportar",
                f"No se pudo escribir el archivo:\n{exc}",
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _feature_label(
        feat: Any,
        fid: int,
        layer: QgsVectorLayer,
    ) -> str:
        """Build a human-readable label for a feature in the combo.

        Tries common display attribute names first; falls back to
        ``"FID {n}"``.
        """
        display_fields = ("owner", "nombre", "name", "parcela", "label")
        for attr_name in display_fields:
            idx = layer.fields().indexFromName(attr_name)
            if idx >= 0:
                val = feat.attribute(idx)
                if val is not None and str(val).strip():
                    return f"{val} (FID {fid})"
        return f"FID {fid}"

    # ------------------------------------------------------------------
    # QSettings persistence
    # ------------------------------------------------------------------

    def _save_settings(self) -> None:
        """Persist the current dock state to QSettings."""
        s = QSettings(_ORG, _APP)

        layer = self.layer_combo.currentLayer()
        if layer is not None:
            s.setValue(_KEY_LAST_LAYER, layer.id())
        else:
            s.remove(_KEY_LAST_LAYER)

        col = self.colindancia_combo.currentLayer()
        if col is not None:
            s.setValue(_KEY_LAST_COL_LAYER, col.id())
        else:
            s.remove(_KEY_LAST_COL_LAYER)

        s.setValue(_KEY_LAST_TEMPLATE, self.template_combo.currentText())
        s.setValue(_KEY_GEOMETRY, self.saveGeometry())
        s.setValue(_KEY_STATE, self.saveState())

    def _restore_settings(self) -> None:
        """Restore the last dock state from QSettings."""
        s = QSettings(_ORG, _APP)

        # Restore layer
        layer_id: str | None = s.value(_KEY_LAST_LAYER, None)
        if layer_id:
            layer = QgsProject.instance().mapLayer(layer_id)
            if isinstance(layer, QgsVectorLayer):
                self.layer_combo.setLayer(layer)

        # Restore colindancia layer
        col_id: str | None = s.value(_KEY_LAST_COL_LAYER, None)
        if col_id:
            col = QgsProject.instance().mapLayer(col_id)
            if isinstance(col, QgsVectorLayer):
                self.colindancia_combo.setLayer(col)

        # Restore template
        template: str | None = s.value(_KEY_LAST_TEMPLATE, "")
        if template:
            idx = self.template_combo.findText(template)
            if idx >= 0:
                self.template_combo.setCurrentIndex(idx)

        # Restore geometry and state
        geometry = s.value(_KEY_GEOMETRY)
        if geometry:
            self.restoreGeometry(geometry)
        state = s.value(_KEY_STATE)
        if state:
            self.restoreState(state)
