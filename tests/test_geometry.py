"""Tests for engine/geometry.py — vertex extraction and NW ordering."""

import math

import pytest
from qgis.core import (
    QgsGeometry,
    QgsLineString,
    QgsPoint,
    QgsPolygon,
    QgsRectangle,
)

from derrotero_catastral.engine.geometry import (
    extract_interior_rings,
    extract_vertices,
    linearize_curve,
    order_nw,
    remove_collinear,
)
from derrotero_catastral.engine.types import Vertex


# ---------------------------------------------------------------------------
# order_nw
# ---------------------------------------------------------------------------

class TestOrderNW:
    """order_nw(vertices) — reorder starting from NW corner."""

    def test_rectangle_nw_first(self):
        """Starting vertex is NW: max Y, tiebreaker min X."""
        vertices = [
            Vertex(0, 0.0, 0.0),
            Vertex(1, 100.0, 0.0),
            Vertex(2, 100.0, 100.0),
            Vertex(3, 0.0, 100.0),
        ]
        result = order_nw(vertices)
        assert result[0] == Vertex(3, 0.0, 100.0)  # NW (max Y=100, min X=0)
        # preserves original winding: NW → SW → SE → NE
        assert [v.index for v in result] == [3, 0, 1, 2]

    def test_tie_same_y_different_x(self):
        """Tie-breaking: same Y height, picks min X."""
        vertices = [
            Vertex(0, 20.0, 100.0),
            Vertex(1, 10.0, 100.0),
            Vertex(2, 10.0, 0.0),
            Vertex(3, 20.0, 0.0),
        ]
        result = order_nw(vertices)
        assert result[0] == Vertex(1, 10.0, 100.0)  # min X among max Y

    def test_single_vertex_returns_same(self):
        """Single vertex returns unchanged."""
        vertices = [Vertex(0, 5.0, 5.0)]
        assert order_nw(vertices) == vertices

    def test_two_vertices_preserves_order(self):
        """Two vertices preserve their relative order, NW first."""
        vertices = [Vertex(0, 10.0, 20.0), Vertex(1, 10.0, 10.0)]
        result = order_nw(vertices)
        assert result[0] == Vertex(0, 10.0, 20.0)  # higher Y is NW

    def test_irregular_polygon_nw(self):
        """Irregular pentagon: NW is the vertex with highest Y, min X."""
        vertices = [
            Vertex(0, 50.0, 30.0),
            Vertex(1, 70.0, 80.0),
            Vertex(2, 40.0, 90.0),
            Vertex(3, 20.0, 60.0),
            Vertex(4, 30.0, 20.0),
        ]
        result = order_nw(vertices)
        # max Y = 90.0 at index 2 (x=40.0); no tie
        assert result[0] == Vertex(2, 40.0, 90.0)

    def test_preserves_winding_clockwise(self):
        """Rotating does not change the winding order."""
        vertices = [
            Vertex(0, 0.0, 0.0),
            Vertex(1, 100.0, 0.0),
            Vertex(2, 100.0, 100.0),
            Vertex(3, 0.0, 100.0),
        ]
        result = order_nw(vertices)
        # Should be NW → SW → SE → NE (preserving original winding)
        expected_cycle = [
            Vertex(3, 0.0, 100.0),
            Vertex(0, 0.0, 0.0),
            Vertex(1, 100.0, 0.0),
            Vertex(2, 100.0, 100.0),
        ]
        assert result == expected_cycle

    def test_all_vertices_returned(self):
        """No vertices are lost during reordering."""
        vertices = [
            Vertex(0, 10.0, 20.0),
            Vertex(1, 30.0, 40.0),
            Vertex(2, 50.0, 60.0),
        ]
        result = order_nw(vertices)
        assert len(result) == 3
        assert set(v.index for v in result) == {0, 1, 2}


# ---------------------------------------------------------------------------
# extract_vertices
# ---------------------------------------------------------------------------

class TestExtractVertices:
    """extract_vertices(geom) — extract vertices from QgsPolygon."""

    def test_square_from_qgsrectangle(self):
        """QgsRectangle produces 4 vertices from exterior ring."""
        geom = QgsGeometry.fromRect(QgsRectangle(0, 0, 100, 100))
        polygon = geom.get()
        vertices = extract_vertices(polygon)
        assert len(vertices) == 4
        # QgsRectangle vertices order: LL, LR, UR, UL → (0,0), (100,0), (100,100), (0,100)
        assert vertices[0] == Vertex(0, 0.0, 0.0)

    def test_empty_geometry_returns_empty(self):
        """Empty polygon returns empty list."""
        polygon = QgsPolygon()
        vertices = extract_vertices(polygon)
        assert vertices == []

    def test_linear_ring_exterior(self):
        """Exterior ring vertices are extracted correctly."""
        ring = QgsLineString([
            QgsPoint(0.0, 0.0),
            QgsPoint(50.0, 0.0),
            QgsPoint(50.0, 50.0),
            QgsPoint(0.0, 50.0),
            QgsPoint(0.0, 0.0),
        ])
        polygon = QgsPolygon(ring)
        vertices = extract_vertices(polygon)
        assert len(vertices) == 4  # closing vertex omitted


# ---------------------------------------------------------------------------
# extract_interior_rings
# ---------------------------------------------------------------------------

class TestExtractInteriorRings:
    """extract_interior_rings(geom) — holes as separate vertex lists."""

    def test_no_holes_returns_empty(self):
        """Polygon without holes returns empty list."""
        ring = QgsLineString([
            QgsPoint(0.0, 0.0),
            QgsPoint(100.0, 0.0),
            QgsPoint(100.0, 100.0),
            QgsPoint(0.0, 100.0),
            QgsPoint(0.0, 0.0),
        ])
        polygon = QgsPolygon(ring)
        holes = extract_interior_rings(polygon)
        assert holes == []

    def test_one_hole_returns_separate_ring(self):
        """Polygon with one hole returns one separate vertex list."""
        exterior = QgsLineString([
            QgsPoint(0.0, 0.0),
            QgsPoint(100.0, 0.0),
            QgsPoint(100.0, 100.0),
            QgsPoint(0.0, 100.0),
            QgsPoint(0.0, 0.0),
        ])
        hole = QgsLineString([
            QgsPoint(25.0, 25.0),
            QgsPoint(75.0, 25.0),
            QgsPoint(75.0, 75.0),
            QgsPoint(25.0, 75.0),
            QgsPoint(25.0, 25.0),
        ])
        polygon = QgsPolygon(exterior, [hole])
        holes = extract_interior_rings(polygon)
        assert len(holes) == 1
        assert len(holes[0]) == 4  # 4 unique vertices

    def test_two_holes(self):
        """Polygon with two holes returns two lists."""
        exterior = QgsLineString([
            QgsPoint(0.0, 0.0),
            QgsPoint(100.0, 0.0),
            QgsPoint(100.0, 100.0),
            QgsPoint(0.0, 100.0),
            QgsPoint(0.0, 0.0),
        ])
        hole1 = QgsLineString([
            QgsPoint(10.0, 10.0),
            QgsPoint(20.0, 10.0),
            QgsPoint(20.0, 20.0),
            QgsPoint(10.0, 20.0),
            QgsPoint(10.0, 10.0),
        ])
        hole2 = QgsLineString([
            QgsPoint(80.0, 80.0),
            QgsPoint(90.0, 80.0),
            QgsPoint(90.0, 90.0),
            QgsPoint(80.0, 90.0),
            QgsPoint(80.0, 80.0),
        ])
        polygon = QgsPolygon(exterior, [hole1, hole2])
        holes = extract_interior_rings(polygon)
        assert len(holes) == 2


# ---------------------------------------------------------------------------
# remove_collinear
# ---------------------------------------------------------------------------

class TestRemoveCollinear:
    """remove_collinear(vertices) — deduplicate collinear vertices."""

    def test_removes_intermediate_collinear(self):
        """Collinear intermediate vertex is removed."""
        vertices = [
            Vertex(0, 0.0, 0.0),
            Vertex(1, 50.0, 0.0),  # collinear: (0,0)→(50,0)→(100,0)
            Vertex(2, 100.0, 0.0),
            Vertex(3, 100.0, 100.0),
            Vertex(4, 0.0, 100.0),
        ]
        result = remove_collinear(vertices)
        assert len(result) == 4
        assert Vertex(1, 50.0, 0.0) not in result

    def test_no_collinear_unchanged(self):
        """No collinear vertices — list unchanged."""
        vertices = [
            Vertex(0, 0.0, 0.0),
            Vertex(1, 100.0, 0.0),
            Vertex(2, 100.0, 100.0),
            Vertex(3, 0.0, 100.0),
        ]
        assert remove_collinear(vertices) == vertices

    def test_three_collinear_keeps_endpoints(self):
        """Only the middle collinear points are removed, endpoints preserved."""
        vertices = [
            Vertex(0, 0.0, 0.0),
            Vertex(1, 25.0, 0.0),
            Vertex(2, 50.0, 0.0),
            Vertex(3, 75.0, 0.0),
            Vertex(4, 100.0, 0.0),
            Vertex(5, 100.0, 100.0),
            Vertex(6, 0.0, 100.0),
        ]
        result = remove_collinear(vertices)
        assert len(result) == 4
        # endpoints preserved
        assert Vertex(0, 0.0, 0.0) in result
        assert Vertex(4, 100.0, 0.0) in result


# ---------------------------------------------------------------------------
# linearize_curve
# ---------------------------------------------------------------------------

class TestLinearizeCurve:
    """linearize_curve(geom) — convert curved segments to straight."""

    def test_straight_ring_unchanged(self):
        """A ring with only straight segments returns same vertex count."""
        ring = QgsLineString([
            QgsPoint(0.0, 0.0),
            QgsPoint(100.0, 0.0),
            QgsPoint(100.0, 100.0),
            QgsPoint(0.0, 100.0),
            QgsPoint(0.0, 0.0),
        ])
        result = linearize_curve(ring)
        assert result.numPoints() == 5

    def test_curved_ring_adds_segments(self):
        """A circular arc produces more straight segments."""
        # Build a circular string: center at (50,50), radius 50, from 0° to 180°
        from qgis.core import QgsGeometry as QgsG

        geom = QgsG.fromWkt("CircularString (100 50, 50 100, 0 50)")
        arc = geom.get()
        linearized = linearize_curve(arc)
        # With 5° tolerance on a 180° arc → at least 30 points
        assert linearized.numPoints() > 30
        # Start and end should be close to original
        start = linearized.startPoint()
        end = linearized.endPoint()
        assert abs(start.x() - 100.0) < 0.001
        assert abs(end.x() - 0.0) < 0.001
