"""Bearing calculations — azimuth, quadrant bearing, cardinal orientation."""


from qgis.core import QgsPointXY

from derrotero_catastral.engine.types import Vertex

# ---------------------------------------------------------------------------
# Azimuth
# ---------------------------------------------------------------------------


def compute_azimuth(a: Vertex, b: Vertex) -> float:
    """Compute the forward azimuth from vertex *a* to vertex *b*.

    Uses ``QgsPointXY.azimuth()`` under the hood and normalises the
    result to [0°, 360°).

    Returns ``float('nan')`` for zero-length segments (identical points).
    """
    if a.x == b.x and a.y == b.y:
        return float("nan")
    p1 = QgsPointXY(a.x, a.y)
    p2 = QgsPointXY(b.x, b.y)
    raw = p1.azimuth(p2)
    return normalize_azimuth(raw)


def normalize_azimuth(raw: float) -> float:
    """Normalise a raw azimuth (range -180..180) to [0°, 360°).

    Values outside the usual range are also wrapped correctly.
    """
    normalised = raw % 360.0
    if normalised < 0:
        normalised += 360.0
    # Handle floating-point values extremely close to 360
    if abs(normalised - 360.0) < 1e-12:
        normalised = 0.0
    return normalised


# ---------------------------------------------------------------------------
# Quadrant bearing (rumbo)
# ---------------------------------------------------------------------------


def _azimuth_to_quadrant(azimut: float) -> tuple[str, float, str]:
    """Split an azimuth into (north_south, angle, east_west)."""
    if 0.0 <= azimut <= 90.0:
        return ("N", azimut, "E")
    if 90.0 < azimut <= 180.0:
        return ("S", 180.0 - azimut, "E")
    if 180.0 < azimut <= 270.0:
        return ("S", azimut - 180.0, "W")
    # 270° < azimuth < 360°
    return ("N", 360.0 - azimut, "W")


def to_quadrant_bearing(azimut: float, dms: bool = False) -> str:
    """Convert a normalised azimuth to a quadrant-bearing string.

    Examples
    --------
    >>> to_quadrant_bearing(45.0)
    'N 45° E'
    >>> to_quadrant_bearing(45.5, dms=True)
    'N 45° 30' 0.0\\" E'
    """
    azimut = azimut % 360.0

    # Due-cardinal shortcuts
    if azimut == 0.0 or azimut == 360.0:
        return "N"
    if azimut == 90.0:
        return "E"
    if azimut == 180.0:
        return "S"
    if azimut == 270.0:
        return "W"

    ns, angle, ew = _azimuth_to_quadrant(azimut)

    if dms:
        dms_str = _to_dms(angle)
        return f"{ns} {dms_str} {ew}"
    return f"{ns} {angle:.0f}° {ew}"


def _to_dms(degrees: float, precision: int = 1) -> str:
    """Convert decimal degrees to degrees-minutes-seconds string.

    Returns a string like ``"45° 30' 0.0\\""``.
    """
    deg = int(degrees)
    remainder = abs(degrees - deg) * 60
    minutes = int(remainder)
    seconds = (remainder - minutes) * 60
    return f"{deg}° {minutes}' {seconds:.{precision}f}\""


# ---------------------------------------------------------------------------
# Cardinal orientation
# ---------------------------------------------------------------------------

_CARDINAL_ES: list[tuple[float, float, str]] = [
    (337.5, 360.0, "Norte"),
    (0.0, 22.5, "Norte"),
    (22.5, 67.5, "Noreste"),
    (67.5, 112.5, "Este"),
    (112.5, 157.5, "Sureste"),
    (157.5, 202.5, "Sur"),
    (202.5, 247.5, "Suroeste"),
    (247.5, 292.5, "Oeste"),
    (292.5, 337.5, "Noroeste"),
]

_CARDINAL_EN: list[tuple[float, float, str]] = [
    (337.5, 360.0, "North"),
    (0.0, 22.5, "North"),
    (22.5, 67.5, "Northeast"),
    (67.5, 112.5, "East"),
    (112.5, 157.5, "Southeast"),
    (157.5, 202.5, "South"),
    (202.5, 247.5, "Southwest"),
    (247.5, 292.5, "West"),
    (292.5, 337.5, "Northwest"),
]

_CARDINAL_CO: list[tuple[float, float, str]] = [
    (337.5, 360.0, "Norte"),
    (0.0, 22.5, "Norte"),
    (22.5, 67.5, "Nororiente"),
    (67.5, 112.5, "Oriente"),
    (112.5, 157.5, "Suroriente"),
    (157.5, 202.5, "Sur"),
    (202.5, 247.5, "Suroccidente"),
    (247.5, 292.5, "Occidente"),
    (292.5, 337.5, "Noroccidente"),
]

_LOCALES: dict[str, list[tuple[float, float, str]]] = {
    "es": _CARDINAL_ES,
    "en": _CARDINAL_EN,
    "co": _CARDINAL_CO,
}


def to_cardinal(azimut: float, locale: str = "es") -> str:
    """Map a normalised azimuth to one of the 8 cardinal directions.

    Parameters
    ----------
    azimut
        Normalised azimuth in [0°, 360°).
    locale
        Language locale — ``"es"`` (Spanish, default), ``"en"`` (English),
        or ``"co"`` (Colombian Spanish variants).

    Returns
    -------
    str
        Cardinal direction label (e.g. ``"Norte"``, ``"Northeast"``).
    """
    azimut = azimut % 360.0
    table = _LOCALES.get(locale, _CARDINAL_ES)
    for lo, hi, label in table:
        if lo <= azimut < hi:
            return label
    # Fallback (shouldn't happen with valid input)
    return "Norte"
