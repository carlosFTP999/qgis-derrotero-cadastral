"""Read-only preview widget for the generated derrotero text."""

from qgis.PyQt.QtWidgets import QPlainTextEdit


class DerroteroPreview(QPlainTextEdit):
    """A read-only text widget for previewing the generated derrotero.

    Provides convenience methods to set and retrieve the preview content,
    making the export workflow straightforward.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText(
            "Seleccione un predio y presione \"Generar Derrotero\"..."
        )
        # Monospace font for tabular blueprints (generic.j2)
        font = self.font()
        font.setFamily("Courier New, Consolas, monospace")
        font.setPointSize(10)
        self.setFont(font)
        self.setMinimumHeight(150)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_text(self, text: str) -> None:
        """Replace the preview content with *text*.

        Parameters
        ----------
        text
            The rendered derrotero string to display.
        """
        self.setPlainText(text)

    def get_text(self) -> str:
        """Return the current preview content.

        Returns
        -------
        str
            The displayed derrotero text (may be empty).
        """
        return self.toPlainText()

    def clear_text(self) -> None:
        """Clear the preview content."""
        self.clear()
