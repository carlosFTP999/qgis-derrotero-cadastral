"""Tests for engine/bearing.py — azimuth, quadrant bearing, cardinal orientation."""

import math

import pytest
from qgis.core import QgsPointXY

from derrotero_catastral.engine.bearing import (
    compute_azimuth,
    normalize_azimuth,
    to_cardinal,
    to_quadrant_bearing,
)
from derrotero_catastral.engine.types import Vertex


# ---------------------------------------------------------------------------
# normalize_azimuth
# ---------------------------------------------------------------------------

class TestNormalizeAzimuth:
    """normalize_azimuth(raw) — convert -180..180 to 0..360."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (0.0, 0.0),
            (45.0, 45.0),
            (90.0, 90.0),
            (180.0, 180.0),
            (-45.0, 315.0),
            (-90.0, 270.0),
            (-135.0, 225.0),
            (-180.0, 180.0),
            (360.0, 0.0),
            (400.0, 40.0),
            (-360.0, 0.0),
            (-400.0, 320.0),
        ],
    )
    def test_normalize(self, raw, expected):
        assert normalize_azimuth(raw) == pytest.approx(expected, abs=1e-10)


# ---------------------------------------------------------------------------
# compute_azimuth
# ---------------------------------------------------------------------------

class TestComputeAzimuth:
    """compute_azimuth(a, b) — forward azimuth using QgsPointXY."""

    def test_due_north(self):
        """A(0,0)→B(0,1): azimuth should be 0.0 (due North)."""
        a = Vertex(0, 0.0, 0.0)
        b = Vertex(1, 0.0, 1.0)
        assert compute_azimuth(a, b) == pytest.approx(0.0, abs=1e-10)

    def test_due_east(self):
        """A(0,0)→B(1,0): azimuth should be 90.0."""
        a = Vertex(0, 0.0, 0.0)
        b = Vertex(1, 1.0, 0.0)
        assert compute_azimuth(a, b) == pytest.approx(90.0, abs=1e-10)

    @pytest.mark.parametrize(
        ("ax", "ay", "bx", "by", "expected"),
        [
            (0.0, 0.0, 1.0, 1.0, 45.0),     # NE  (dx=1, dy=1)
            (0.0, 0.0, 1.0, -1.0, 135.0),   # SE  (dx=1, dy=-1)
            (0.0, 0.0, -1.0, 1.0, 315.0),   # NW  (dx=-1, dy=1)
            (0.0, 0.0, -1.0, -1.0, 225.0),  # SW  (dx=-1, dy=-1)
        ],
    )
    def test_four_quadrants(self, ax, ay, bx, by, expected):
        a = Vertex(0, ax, ay)
        b = Vertex(1, bx, by)
        assert compute_azimuth(a, b) == pytest.approx(expected, abs=1e-10)

    def test_zero_length_segment(self):
        """Same point should return NaN (sentinel for invalid)."""
        a = Vertex(0, 5.0, 5.0)
        b = Vertex(1, 5.0, 5.0)
        result = compute_azimuth(a, b)
        assert math.isnan(result)


# ---------------------------------------------------------------------------
# to_quadrant_bearing
# ---------------------------------------------------------------------------

class TestToQuadrantBearing:
    """to_quadrant_bearing(azimut) — azimuth to compass bearing."""

    def test_ne_quadrant(self):
        """NE: N 45° E."""
        assert to_quadrant_bearing(45.0) == "N 45° E"

    def test_se_quadrant(self):
        """SE: S 45° E."""
        assert to_quadrant_bearing(135.0) == "S 45° E"

    def test_sw_quadrant(self):
        """SW: S 45° W."""
        assert to_quadrant_bearing(225.0) == "S 45° W"

    def test_nw_quadrant(self):
        """NW: N 45° W."""
        assert to_quadrant_bearing(315.0) == "N 45° W"

    @pytest.mark.parametrize(
        ("azimut", "expected"),
        [
            (0.0, "N"),          # due North — no E/W suffix
            (90.0, "E"),         # due East — no N/S prefix
            (180.0, "S"),        # due South
            (270.0, "W"),        # due West
            (30.0, "N 30° E"),
            (120.0, "S 60° E"),
            (210.0, "S 30° W"),
            (300.0, "N 60° W"),
        ],
    )
    def test_cardinal_and_quadrant_edges(self, azimut, expected):
        assert to_quadrant_bearing(azimut) == expected

    def test_dms_format(self):
        """45.5° → N 45° 30' 0.0\" E."""
        assert to_quadrant_bearing(45.5, dms=True) == "N 45° 30' 0.0\" E"

    def test_dms_edge_azimuth(self):
        """0.5° → N 0° 30' 0.0\" E."""
        result = to_quadrant_bearing(0.5, dms=True)
        assert result == "N 0° 30' 0.0\" E"

    def test_zero_azimuth_rounding(self):
        """Input near 0 displays 0."""
        # DMS of a small value
        result = to_quadrant_bearing(0.05, dms=True)
        assert "0°" in result


# ---------------------------------------------------------------------------
# to_cardinal
# ---------------------------------------------------------------------------

class TestToCardinal:
    """to_cardinal(azimut, locale) — azimuth to 8-point cardinal."""

    @pytest.mark.parametrize(
        ("azimut", "expected_es", "expected_en"),
        [
            (0.0, "Norte", "North"),
            (45.0, "Noreste", "Northeast"),
            (90.0, "Este", "East"),
            (135.0, "Sureste", "Southeast"),
            (180.0, "Sur", "South"),
            (225.0, "Suroeste", "Southwest"),
            (270.0, "Oeste", "West"),
            (315.0, "Noroeste", "Northwest"),
        ],
    )
    def test_main_directions(self, azimut, expected_es, expected_en):
        assert to_cardinal(azimut, locale="es") == expected_es
        assert to_cardinal(azimut, locale="en") == expected_en

    def test_edge_norte_lower(self):
        """337.5° → Norte."""
        assert to_cardinal(337.5) == "Norte"

    def test_edge_norte_upper_exclusive(self):
        """22.5° is the start of Noreste range, not Norte."""
        assert to_cardinal(22.5) == "Noreste"
        assert to_cardinal(22.4999) == "Norte"

    def test_edge_noreste_lower(self):
        """22.5001° → Noreste."""
        assert to_cardinal(22.5001) == "Noreste"

    def test_edge_noreste_upper_exclusive(self):
        """67.5° is the start of Este range, not Noreste."""
        assert to_cardinal(67.5) == "Este"
        assert to_cardinal(67.4999) == "Noreste"

    def test_just_below_north(self):
        """337.4° → Noroeste."""
        assert to_cardinal(337.4) == "Noroeste"

    def test_locale_co(self):
        """co locale provides Colombian variants."""
        result = to_cardinal(0.0, locale="co")
        assert isinstance(result, str)
        assert len(result) > 0
