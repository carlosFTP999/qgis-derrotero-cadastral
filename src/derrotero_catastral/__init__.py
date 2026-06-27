"""Derrotero Catastral — QGIS plugin for cadastral traverse generation."""


def classFactory(iface):  # noqa: N802
    """Load and return the plugin instance.

    QGIS calls this function when loading the plugin.
    """
    from derrotero_catastral.derrotero_catastral import DerroteroCatastralPlugin

    return DerroteroCatastralPlugin(iface)
