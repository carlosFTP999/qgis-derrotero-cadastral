"""Colindancia detection using QgsSpatialIndex.

Detects which neighbouring parcels share an edge with each perimeter
segment of the source parcel.  Supports partial colindancias (multiple
neighbours along one segment) and gracefully handles open faces.
"""


from qgis.core import (
    QgsGeometry,
    QgsPoint,
    QgsPointXY,
    QgsSpatialIndex,
    QgsVectorLayer,
    QgsWkbTypes,
)

from derrotero_catastral.engine.types import Colindancia


def build_index(layer: QgsVectorLayer) -> QgsSpatialIndex:
    """Build a :class:`QgsSpatialIndex` from a colindancia (neighbour parcels) layer.

    Features without a geometry are silently skipped.

    Parameters
    ----------
    layer
        A polygon vector layer representing neighbouring parcels.

    Returns
    -------
    QgsSpatialIndex
        Spatial index containing all features with valid geometries.
    """
    index = QgsSpatialIndex()
    for feat in layer.getFeatures():
        if feat.hasGeometry():
            index.addFeature(feat)
    return index


def find_colindancias(
    segment_idx: int,
    segment: tuple[float, float, float, float],
    index: QgsSpatialIndex,
    layer: QgsVectorLayer,
    max_results: int = 5,
) -> list[Colindancia]:
    """Find colindancias for a single perimeter segment.

    The segment geometry is intersected with each candidate polygon
    returned by the spatial index.  Only line-geometry intersections
    (length > 0) count as valid colindancias; point/vertex touches are
    excluded.

    Parameters
    ----------
    segment_idx
        Zero-based index of this segment in the polygon perimeter.
    segment
        ``(x1, y1, x2, y2)`` coordinates of the segment.
    index
        :class:`QgsSpatialIndex` built from the neighbour layer
        (see :func:`build_index`).
    layer
        The neighbour vector layer (used to retrieve feature attributes).
    max_results
        Maximum number of candidates to return from the spatial-index
        nearest-neighbour query (default ``5``).

    Returns
    -------
    list[Colindancia]
        One :class:`Colindancia` per detected adjacent parcel.  Empty
        list when no parcel shares a proper edge with the segment.
    """
    x1, y1, x2, y2 = segment

    # Midpoint of the segment — used as the spatial index query point
    mid_point = QgsPointXY((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    # Build a geometry from the segment for intersection tests
    segment_geom = QgsGeometry.fromPolyline([
        QgsPoint(x1, y1),
        QgsPoint(x2, y2),
    ])

    candidate_fids = index.nearestNeighbor(mid_point, max_results)

    results: list[Colindancia] = []
    for fid in candidate_fids:
        feat = layer.getFeature(fid)
        if not feat.hasGeometry():
            continue

        neighbour_geom = feat.geometry()
        intersection = segment_geom.intersection(neighbour_geom)

        # Exclude empty, point-only, and polygon intersections
        if intersection.isEmpty():
            continue
        if intersection.type() != QgsWkbTypes.LineGeometry:
            continue

        overlap_length = intersection.length()
        if overlap_length <= 0.0:
            continue

        neighbour_owner: str | None = feat.attribute("owner")
        results.append(Colindancia(
            segment_idx=segment_idx,
            neighbor_fid=fid,
            neighbor_owner=neighbour_owner,
            overlap_length=overlap_length,
        ))

    return results
