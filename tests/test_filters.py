"""Tests for template/filters.py — custom Jinja2 filters."""

import pytest

from derrotero_catastral.template.filters import (
    format_number,
    to_cardinal,
    to_dms,
    to_quadrant,
)


# ---------------------------------------------------------------------------
# format_number
# ---------------------------------------------------------------------------


class TestFormatNumber:
    """format_number(value, decimals, decimal_sep, thousands_sep)."""

    def test_default_params(self):
        """Default: 3 decimals, comma decimal, dot thousand."""
        assert format_number(1234.5678) == "1.234,568"

    def test_integer_value(self):
        """Integer with default decimals → .000."""
        assert format_number(42.0) == "42,000"

    def test_decimal_sep_dot(self):
        """Decimal separator '.' and thousand separator ',' (English style)."""
        assert format_number(1234.5, decimal_sep=".", thousands_sep=",") == "1,234.500"

    def test_zero_decimals(self):
        """No decimal places."""
        assert format_number(99.9, decimals=0) == "100"

    def test_no_thousands_sep(self):
        """Small number without thousand separator."""
        assert format_number(123.456) == "123,456"

    def test_large_number_with_thousands(self):
        """Very large number with thousand separators."""
        result = format_number(1234567.8912, decimals=2)
        assert result == "1.234.567,89"

    def test_negative_number(self):
        """Negative values work correctly."""
        assert format_number(-1234.56, decimals=1) == "-1.234,6"

    def test_zero_value(self):
        """Zero is handled."""
        assert format_number(0.0) == "0,000"

    def test_no_decimal_thousands(self):
        """decimals=0 with large number."""
        assert format_number(999999.99, decimals=0) == "1.000.000"


# ---------------------------------------------------------------------------
# to_dms
# ---------------------------------------------------------------------------


class TestToDms:
    """to_dms(degrees, precision) — decimal degrees → DMS string."""

    def test_exact_degree(self):
        """45.0° → 45° 0' 0.0\"."""
        assert to_dms(45.0) == "45° 0' 0.0\""

    def test_exact_minute(self):
        """45.5° → 45° 30' 0.0\"."""
        assert to_dms(45.5) == "45° 30' 0.0\""

    def test_with_seconds_remainder(self):
        """45.5333° → 45° 32' 0.0\" approx (need exact)."""
        result = to_dms(45.5333, precision=1)
        assert result.startswith("45° 31'")
        assert result.endswith('"')

    def test_precision_two(self):
        """Custom precision=2 → seconds with 2 decimals."""
        result = to_dms(45.5333, precision=2)
        assert '"' in result
        parts = result.split()
        assert len(parts) == 3  # "45°" "31'" "59.88""

    def test_zero_degrees(self):
        """0° → 0° 0' 0.0\"."""
        assert to_dms(0.0) == "0° 0' 0.0\""

    def test_negative_degrees(self):
        """Negative values work."""
        assert to_dms(-45.5) == "-45° 30' 0.0\""

    def test_above_360(self):
        """Values > 360 are converted anyway."""
        result = to_dms(361.0)
        assert "361°" in result


# ---------------------------------------------------------------------------
# to_quadrant
# ---------------------------------------------------------------------------


class TestToQuadrant:
    """to_quadrant(azimut, dms) — azimuth → quadrant bearing."""

    def test_ne_quadrant(self):
        """NE: N 45° E."""
        assert to_quadrant(45.0) == "N 45° E"

    def test_se_quadrant(self):
        """SE: S 45° E."""
        assert to_quadrant(135.0) == "S 45° E"

    def test_sw_quadrant(self):
        """SW: S 45° W."""
        assert to_quadrant(225.0) == "S 45° W"

    def test_nw_quadrant(self):
        """NW: N 45° W."""
        assert to_quadrant(315.0) == "N 45° W"

    def test_cardinal_north(self):
        """0° → N."""
        assert to_quadrant(0.0) == "N"

    def test_cardinal_east(self):
        """90° → E."""
        assert to_quadrant(90.0) == "E"

    def test_cardinal_south(self):
        """180° → S."""
        assert to_quadrant(180.0) == "S"

    def test_cardinal_west(self):
        """270° → W."""
        assert to_quadrant(270.0) == "W"

    def test_dms_mode(self):
        """45.5° dms=True → N 45° 30' 0.0\" E."""
        result = to_quadrant(45.5, dms=True)
        assert result == "N 45° 30' 0.0\" E"

    def test_dms_small_azimuth(self):
        """0.5° dms=True."""
        result = to_quadrant(0.5, dms=True)
        assert result == "N 0° 30' 0.0\" E"

    def test_quadrant_just_below_90(self):
        """89.9° rounds to 90° → N 90° E."""
        assert to_quadrant(89.9) == "N 90° E"


# ---------------------------------------------------------------------------
# to_cardinal
# ---------------------------------------------------------------------------


class TestToCardinal:
    """to_cardinal(azimut, locale) — azimuth → 8-point cardinal."""

    @pytest.mark.parametrize(
        ("azimut", "expected"),
        [
            (0.0, "Norte"),
            (45.0, "Noreste"),
            (90.0, "Este"),
            (135.0, "Sureste"),
            (180.0, "Sur"),
            (225.0, "Suroeste"),
            (270.0, "Oeste"),
            (315.0, "Noroeste"),
        ],
    )
    def test_eight_directions_es(self, azimut, expected):
        """8 cardinal directions in Spanish."""
        assert to_cardinal(azimut, locale="es") == expected

    @pytest.mark.parametrize(
        ("azimut", "expected"),
        [
            (0.0, "North"),
            (90.0, "East"),
            (180.0, "South"),
            (270.0, "West"),
        ],
    )
    def test_main_directions_en(self, azimut, expected):
        """Main cardinal directions in English."""
        assert to_cardinal(azimut, locale="en") == expected

    def test_locale_co(self):
        """Colombian locale works."""
        result = to_cardinal(0.0, locale="co")
        assert isinstance(result, str)
        assert len(result) > 0
        # Colombian Spanish uses "Nororiente" for NE
        assert to_cardinal(45.0, locale="co") == "Nororiente"

    def test_edge_337_5_is_norte(self):
        """337.5° → Norte (boundary)."""
        assert to_cardinal(337.5) == "Norte"

    def test_edge_22_5_is_not_norte(self):
        """22.5° is the start of Noreste."""
        assert to_cardinal(22.5) == "Noreste"
        # Just below 22.5 should be Norte
        assert to_cardinal(22.4999) == "Norte"

    def test_unknown_locale_falls_back_to_es(self):
        """Unknown locale defaults to Spanish."""
        result = to_cardinal(45.0, locale="de")
        assert result == "Noreste"
