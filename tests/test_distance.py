"""Tests for engine/distance.py — geodetic distance and cumulative totals."""

import math

import pytest
from qgis.core import QgsCoordinateReferenceSystem, QgsDistanceArea, QgsPointXY

from derrotero_catastral.engine.distance import (
    compute_distance,
    compute_totals,
    round_distance,
)
from derrotero_catastral.engine.types import SegmentData, Vertex


# ---------------------------------------------------------------------------
# round_distance
# ---------------------------------------------------------------------------

class TestRoundDistance:
    """round_distance(value, precision) — configurable rounding."""

    def test_default_precision(self):
        """Default precision (3) rounds to mm."""
        assert round_distance(100.12345) == pytest.approx(100.123, abs=1e-10)

    def test_custom_precision_zero(self):
        """Precision 0 rounds to integer."""
        assert round_distance(100.12345, precision=0) == pytest.approx(100.0, abs=1e-10)

    def test_custom_precision_two(self):
        """Precision 2 rounds to cm."""
        assert round_distance(100.12345, precision=2) == pytest.approx(100.12, abs=1e-10)

    def test_negative_precision_falls_back(self):
        """Negative precision falls back to default 3."""
        assert round_distance(100.12345, precision=-1) == pytest.approx(100.123, abs=1e-10)

    def test_zero_distance(self):
        """Zero distance stays 0.0."""
        assert round_distance(0.0) == pytest.approx(0.0, abs=1e-10)


# ---------------------------------------------------------------------------
# compute_distance
# ---------------------------------------------------------------------------

class TestComputeDistance:
    """compute_distance(a, b, crs) — geodetic distance via QgsDistanceArea."""

    @pytest.fixture
    def wgs84(self):
        return QgsCoordinateReferenceSystem("EPSG:4326")

    @pytest.fixture
    def utm_zone(self):
        return QgsCoordinateReferenceSystem("EPSG:32721")  # UTM 21S (meter)

    def test_known_distance_utm(self, utm_zone):
        """100m east in UTM should give ~100m."""
        a = Vertex(0, 500000.0, 7000000.0)
        b = Vertex(1, 500100.0, 7000000.0)
        result = compute_distance(a, b, utm_zone)
        assert result == pytest.approx(100.0, abs=0.1)  # within 10cm

    def test_known_distance_wgs84(self, wgs84):
        """Approx 1° latitude at equator ~111.32 km."""
        a = Vertex(0, -58.5, -34.5)  # Buenos Aires area
        b = Vertex(1, -58.5, -34.0)  # ~0.5° north
        result = compute_distance(a, b, wgs84)
        # ~55.5 km for 0.5° latitude at -34.5°
        assert result == pytest.approx(55500.0, abs=500.0)

    def test_zero_length_segment(self, utm_zone):
        """Same point returns 0.0."""
        a = Vertex(0, 100.0, 200.0)
        b = Vertex(1, 100.0, 200.0)
        assert compute_distance(a, b, utm_zone) == pytest.approx(0.0, abs=1e-6)

    def test_planar_vs_ellipsoidal_different(self, wgs84):
        """Planar and ellipsoidal modes give different results for WGS84."""
        a = Vertex(0, -58.5, -34.5)
        b = Vertex(1, -58.0, -34.0)
        ellip = compute_distance(a, b, wgs84, ellipsoidal=True)
        planar = compute_distance(a, b, wgs84, ellipsoidal=False)
        # For WGS84 lat/lon over ~50km, the difference should exist
        assert abs(ellip - planar) > 1.0  # at least 1m difference

    def test_ellipsoidal_true_by_default(self, wgs84):
        """Default is ellipsoidal=True."""
        a = Vertex(0, -58.5, -34.5)
        b = Vertex(1, -58.5, -34.0)
        default = compute_distance(a, b, wgs84)
        explicit = compute_distance(a, b, wgs84, ellipsoidal=True)
        assert default == pytest.approx(explicit, abs=1e-6)


# ---------------------------------------------------------------------------
# compute_totals
# ---------------------------------------------------------------------------

class TestComputeTotals:
    """compute_totals(segments) — cumulative distance sum."""

    def test_two_segments_sum(self):
        """10.123 + 20.456 = 30.579."""
        segments = [
            SegmentData(0, 1, 0, 0, 10, 0, 10.123, 90.0, "N 90° E", "Este", None),
            SegmentData(1, 2, 10, 0, 10, 20, 20.456, 0.0, "N", "Norte", None),
        ]
        assert compute_totals(segments) == pytest.approx(30.579, abs=1e-10)

    def test_single_segment(self):
        """Single segment = its distance."""
        segments = [
            SegmentData(0, 1, 0, 0, 100, 0, 100.0, 90.0, "N 90° E", "Este", None),
        ]
        assert compute_totals(segments) == pytest.approx(100.0, abs=1e-10)

    def test_empty_segments_returns_zero(self):
        """Empty list returns 0.0."""
        assert compute_totals([]) == pytest.approx(0.0, abs=1e-10)

    def test_many_segments_accumulated(self):
        """N segments with 1.0 each → N."""
        segments = [
            SegmentData(i, i + 1, 0, 0, 0, 0, 1.0, 0.0, "N", "Norte", None)
            for i in range(10)
        ]
        assert compute_totals(segments) == pytest.approx(10.0, abs=1e-10)

    def test_mixed_precision_raw_values(self):
        """Raw values are summed, then rounded once (not per-segment)."""
        segments = [
            SegmentData(0, 1, 0, 0, 0, 0, 1.234, 0.0, "N", "Norte", None),
            SegmentData(1, 2, 0, 0, 0, 0, 2.345, 0.0, "N", "Norte", None),
        ]
        assert compute_totals(segments) == pytest.approx(3.579, abs=1e-10)
