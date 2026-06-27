"""Plugin bootstrap and lifecycle management."""

import os

from qgis.core import QgsApplication
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QLocale, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from derrotero_catastral.gui.dock import DerroteroDock
from derrotero_catastral.processing.pipeline import PipelineOrchestrator

i18n = QTranslator()


class DerroteroCatastralPlugin:
    """Main plugin class for Derrotero Catastral.

    Manages the plugin lifecycle: init, GUI setup, and cleanup.
    Creates and registers the dock widget as the primary user interface.
    """

    def __init__(self, iface: QgisInterface) -> None:
        self.iface = iface
        self.plugin_dir: str = os.path.dirname(os.path.abspath(__file__))
        self.dock: DerroteroDock | None = None
        self.pipeline: PipelineOrchestrator | None = None
        self._action: QAction | None = None
        self._setup_translation()

    def _setup_translation(self) -> None:
        """Configure the Qt translator from the locale file."""
        locale = QLocale.system().name()
        locale_path = os.path.join(
            self.plugin_dir, "i18n", f"derrotero_catastral_{locale}.qm"
        )
        if os.path.exists(locale_path):
            i18n.load(locale_path)
            QgsApplication.instance().installTranslator(i18n)

    def initGui(self) -> None:  # noqa: N802
        """Set up the plugin GUI elements.

        Creates the pipeline orchestrator, the dock widget, and a
        menu action to toggle the dock visibility.
        """
        # Create the pipeline and dock widget
        self.pipeline = PipelineOrchestrator(self.iface)
        self.dock = DerroteroDock(self.iface)

        # Register the dock in QGIS
        from qgis.PyQt.QtCore import Qt

        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        # Menu / toolbar action to show or hide the dock
        icon_path = os.path.join(
            self.plugin_dir, "resources", "icon.svg"
        )
        self._action = QAction(
            QIcon(icon_path) if os.path.exists(icon_path) else QIcon(),
            "Derrotero Catastral",
        )
        self._action.setObjectName("derroteroCatastralAction")
        self._action.setCheckable(True)
        self._action.setChecked(True)
        self._action.triggered.connect(self._toggle_dock)

        self.iface.addToolBarIcon(self._action)
        self.iface.addPluginToMenu("Derrotero Catastral", self._action)

        # Sync action state with dock visibility
        self.dock.visibilityChanged.connect(self._action.setChecked)

    def unload(self) -> None:
        """Clean up plugin resources.

        Removes the dock widget, menu items, and toolbar icon.
        """
        if self.dock is not None:
            self.dock.close()
            self.iface.removeDockWidget(self.dock)
            self.dock = None

        if self._action is not None:
            self.iface.removeToolBarIcon(self._action)
            self.iface.removePluginMenu("Derrotero Catastral", self._action)
            self._action = None

    def _toggle_dock(self, visible: bool) -> None:
        """Show or hide the dock widget."""
        if self.dock is not None:
            self.dock.setVisible(visible)
