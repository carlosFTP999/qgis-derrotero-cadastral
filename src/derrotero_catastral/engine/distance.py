"""Distance calculations — geodetic measurement and cumulative totals."""


from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsDistanceArea,
    QgsPointXY,
)

from derrotero_catastral.engine.types import SegmentData, Vertex


def round_distance(value: float, precision: int = 3) -> float:
    """Round a distance value to a given number of decimal places.

    Falls back to 3 decimal places if *precision* is negative.
    """
    if precision < 0:
        precision = 3
    return round(value, precision)


def compute_distance(
    a: Vertex,
    b: Vertex,
    crs: QgsCoordinateReferenceSystem,
    ellipsoidal: bool = True,
    precision: int = 3,
) -> float:
    """Compute the geodetic distance between two vertices.

    Uses ``QgsDistanceArea`` configured with the given CRS. When
    *ellipsoidal* is ``True`` (default) the measurement uses the
    ellipsoid defined for the CRS; when ``False`` it uses a purely
    planar calculation.

    The result is rounded to *precision* decimal places (default 3).
    """
    p1 = QgsPointXY(a.x, a.y)
    p2 = QgsPointXY(b.x, b.y)

    da = QgsDistanceArea()
    da.setSourceCrs(crs, QgsCoordinateTransformContext())

    if ellipsoidal and crs.isValid() and crs.isGeographic():
        da.setEllipsoid("WGS84")
    else:
        da.setEllipsoid("NONE")

    raw = da.measureLine(p1, p2)
    return round_distance(raw, precision)


def compute_totals(segments: list[SegmentData], precision: int = 3) -> float:
    """Sum the raw distances of all *segments* and round once.

    The sum is rounded to *precision* decimal places as a final step
    (not per-segment).
    """
    total = sum(s.distancia for s in segments)
    return round_distance(total, precision)
