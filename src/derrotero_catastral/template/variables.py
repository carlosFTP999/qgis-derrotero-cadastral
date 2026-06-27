"""Context builder for Jinja2 template rendering.

Assembles a flat dictionary (the *context*) from a list of
:class:`~derrotero_catastral.engine.types.SegmentData` tuples and
optional polygon-level attributes.

The context is designed to be directly passed to
``SandboxedEnvironment.render(**context)``.
"""

from typing import Any

from derrotero_catastral.engine.types import SegmentData

# ---------------------------------------------------------------------------
# Constant
# ---------------------------------------------------------------------------

_COLINDANCIA_PLACEHOLDER = "Vía pública"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_context(
    segments: list[SegmentData],
    polygon_attributes: dict[str, Any] | None = None,
    locale: str = "es",
) -> dict[str, Any]:
    """Build the complete Jinja2 rendering context from segment data.

    Parameters
    ----------
    segments
        Ordered list of computed perimeter segments.
    polygon_attributes
        Optional dict with polygon-level attributes such as
        ``"superficie"`` and ``"referencia_catastral"``.
    locale
        Locale string (e.g. ``"es"``, ``"en"``, ``"co"``).  Currently
        used as pass-through for potential future formatting.

    Returns
    -------
    dict
        Context ready for ``SandboxedEnvironment.render()``.
    """
    attrs = polygon_attributes or {}
    surface = attrs.get("superficie", 0.0)
    if surface is None:
        surface = 0.0
    ref_cat = attrs.get("referencia_catastral", "") or ""

    perimeter = sum(s.distancia for s in segments)

    segmentos = [_segment_to_dict(s) for s in segments]

    context: dict[str, Any] = {
        "segmentos": segmentos,
        "num_total": len(segmentos),
        "superficie": float(surface),
        "perimetro": perimeter,
        "referencia_catastral": ref_cat,
        "locale": locale,
    }

    return context


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _colindancia_display(col: str | None) -> str:
    """Return a display string for a colindancia value.

    Maps ``None`` to ``"Vía pública"`` (open face / public street).
    """
    return _COLINDANCIA_PLACEHOLDER if col is None else col


def _segment_to_dict(s: SegmentData) -> dict[str, Any]:
    """Convert a single SegmentData to a flat dict for the template.

    Adds the helper fields ``colindancia_ref``, ``colindancia_poseedor``,
    ``tipo_colindancia``, and ``colindancia_display`` expected by the
    blueprints.
    """
    col = s.colindancia
    return {
        "v_origen": s.v_origen,
        "v_destino": s.v_destino,
        "x1": s.x1,
        "y1": s.y1,
        "x2": s.x2,
        "y2": s.y2,
        "distancia": s.distancia,
        "azimut": s.azimut,
        "rumbo": s.rumbo,
        "orientacion": s.orientacion,
        "colindancia_ref": col,
        "colindancia_poseedor": col,
        "tipo_colindancia": "via_publica" if col is None else "particular",
        "colindancia_display": _colindancia_display(col),
    }
