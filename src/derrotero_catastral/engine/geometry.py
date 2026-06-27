"""Geometry utilities for vertex extraction and perimeter ordering."""

import math

from qgis.core import QgsAbstractGeometry, QgsCurve, QgsPolygon

from derrotero_catastral.engine.types import Vertex


def extract_vertices(geom: QgsPolygon) -> list[Vertex]:
    """Extract vertices from the exterior ring of a polygon.

    Returns a list of Vertex objects. The closing vertex (identical to
    the first) is omitted.
    """
    exterior = geom.exteriorRing()
    if exterior is None or exterior.numPoints() == 0:
        return []

    count = exterior.numPoints()
    # QGIS rings close back to the first point — skip the duplicate
    if count < 2:
        return []

    vertices = []
    n = count - 1 if _is_closed(exterior) else count
    for i in range(n):
        vertices.append(Vertex(i, exterior.xAt(i), exterior.yAt(i)))
    return vertices


def _is_closed(ring: QgsCurve) -> bool:
    """Check if a ring has a closing vertex (last == first)."""
    if ring.numPoints() < 2:
        return False
    return (
        ring.xAt(0) == ring.xAt(ring.numPoints() - 1)
        and ring.yAt(0) == ring.yAt(ring.numPoints() - 1)
    )


def order_nw(vertices: list[Vertex]) -> list[Vertex]:
    """Reorder vertices starting from the northwesternmost point.

    The NW vertex is the one with the maximum Y (northing), breaking
    ties by selecting the minimum X (easting). The original winding
    order is preserved.
    """
    if len(vertices) <= 1:
        return list(vertices)

    # Find index of NW vertex: max Y, tiebreak min X
    nw_index = 0
    nw_vertex = vertices[0]
    for i, v in enumerate(vertices):
        if v.y > nw_vertex.y or (v.y == nw_vertex.y and v.x < nw_vertex.x):
            nw_index = i
            nw_vertex = v

    # Rotate list so NW vertex is first
    return vertices[nw_index:] + vertices[:nw_index]


def extract_interior_rings(geom: QgsPolygon) -> list[list[Vertex]]:
    """Extract vertices from each interior ring (hole) as separate lists.

    Returns a list of vertex lists, one per interior ring.
    """
    rings: list[list[Vertex]] = []
    for ring_idx in range(geom.numInteriorRings()):
        ring = geom.interiorRing(ring_idx)
        if ring is None or ring.numPoints() < 2:
            continue
        n = ring.numPoints() - 1 if _is_closed(ring) else ring.numPoints()
        vertices = [
            Vertex(i, ring.xAt(i), ring.yAt(i)) for i in range(n)
        ]
        rings.append(vertices)
    return rings


def remove_collinear(vertices: list[Vertex]) -> list[Vertex]:
    """Remove collinear intermediate vertices from a vertex list.

    A vertex is considered collinear if the cross product of the
    vectors formed by its neighbours is zero (within floating-point
    tolerance).
    """
    if len(vertices) <= 2:
        return list(vertices)

    result: list[Vertex] = []
    n = len(vertices)
    for i in range(n):
        prev_v = vertices[(i - 1) % n]
        curr_v = vertices[i]
        next_v = vertices[(i + 1) % n]

        # Cross product of (prev→curr) × (prev→next)
        ax = curr_v.x - prev_v.x
        ay = curr_v.y - prev_v.y
        bx = next_v.x - prev_v.x
        by = next_v.y - prev_v.y
        cross = ax * by - ay * bx

        if abs(cross) > 1e-10:
            result.append(curr_v)

    return result


def linearize_curve(geom: QgsAbstractGeometry) -> QgsAbstractGeometry:
    """Convert curved segments to straight-line approximations.

    For geometries without curves, returns the geometry unchanged.
    Uses a tolerance angle of 5° by default.
    """
    if isinstance(geom, QgsCurve):
        return geom.curveToLine(math.radians(5))
    return geom.clone()
