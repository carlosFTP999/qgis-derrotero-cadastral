"""Custom Jinja2 filters for derrotero template rendering.

Each function in this module is registered as a Jinja2 filter on the
template environment.  Functions are pure — they receive only the value
to transform and optional formatting parameters.
"""


from derrotero_catastral.engine.bearing import (
    _to_dms,
    to_quadrant_bearing,
)
from derrotero_catastral.engine.bearing import (
    to_cardinal as _to_cardinal,
)

# ---------------------------------------------------------------------------
# format_number
# ---------------------------------------------------------------------------


def format_number(
    value: float,
    decimals: int = 3,
    decimal_sep: str = ",",
    thousands_sep: str = ".",
) -> str:
    """Format a number with locale-aware thousand/decimal separators.

    Parameters
    ----------
    value
        The number to format.
    decimals
        Number of decimal places (default ``3``).
    decimal_sep
        Character used as the decimal point (default ``","``).
    thousands_sep
        Character used as the thousands separator (default ``"."``).

    Returns
    -------
    str
        Formatted number string.
    """
    formatted = f"{value:,.{decimals}f}"  # uses '.' decimal, ',' thousand
    # Swap to requested separators
    if decimals > 0:
        int_part, frac_part = formatted.split(".")
        int_part = int_part.replace(",", thousands_sep)
        return f"{int_part}{decimal_sep}{frac_part}"
    else:
        return formatted.replace(",", thousands_sep)


# ---------------------------------------------------------------------------
# to_dms
# ---------------------------------------------------------------------------


def to_dms(degrees: float, precision: int = 1) -> str:
    """Convert decimal degrees to a DMS (degrees-minutes-seconds) string.

    Wraps the internal DMS converter from the bearing engine.

    Parameters
    ----------
    degrees
        Angle in decimal degrees.
    precision
        Number of decimal places for the seconds component (default ``1``).

    Returns
    -------
    str
        DMS string such as ``"45° 30' 0.0\\""``.
    """
    return _to_dms(degrees, precision)


# ---------------------------------------------------------------------------
# to_quadrant
# ---------------------------------------------------------------------------


def to_quadrant(azimut: float, dms: bool = False) -> str:
    """Convert an azimuth to a quadrant-bearing (rumbo) string.

    Delegates to :func:`~derrotero_catastral.engine.bearing.to_quadrant_bearing`.

    Parameters
    ----------
    azimut
        Normalised azimuth in [0°, 360°).
    dms
        When ``True`` the angle part is rendered in DMS notation
        (default ``False``).

    Returns
    -------
    str
        Quadrant bearing string such as ``"N 45° E"``.
    """
    return to_quadrant_bearing(azimut, dms=dms)


# ---------------------------------------------------------------------------
# to_cardinal
# ---------------------------------------------------------------------------


def to_cardinal(azimut: float, locale: str = "es") -> str:
    """Map an azimuth to one of the 8 cardinal directions.

    Delegates to :func:`~derrotero_catastral.engine.bearing.to_cardinal`.

    Parameters
    ----------
    azimut
        Normalised azimuth in [0°, 360°).
    locale
        Language locale (``"es"``, ``"en"``, or ``"co"``).

    Returns
    -------
    str
        Cardinal direction label.
    """
    return _to_cardinal(azimut, locale)
