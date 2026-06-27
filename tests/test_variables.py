"""Tests for template/variables.py — context building for Jinja2 rendering."""

import pytest

from derrotero_catastral.engine.types import SegmentData
from derrotero_catastral.template.variables import build_context


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SEG_1 = SegmentData(
    v_origen=0, v_destino=1,
    x1=0.0, y1=0.0, x2=100.0, y2=0.0,
    distancia=100.0, azimut=90.0, rumbo="E", orientacion="Este",
    colindancia="Juan Pérez",
)

SEG_2 = SegmentData(
    v_origen=1, v_destino=2,
    x1=100.0, y1=0.0, x2=100.0, y2=100.0,
    distancia=100.0, azimut=0.0, rumbo="N", orientacion="Norte",
    colindancia=None,
)

SEG_3 = SegmentData(
    v_origen=2, v_destino=3,
    x1=100.0, y1=100.0, x2=0.0, y2=100.0,
    distancia=100.0, azimut=270.0, rumbo="W", orientacion="Oeste",
    colindancia="María López",
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBuildContext:
    """build_context(segments, polygon_attributes, locale)."""

    def test_three_segments_produces_three_entries(self):
        """3 segments → 3 entries in 'segmentos'."""
        ctx = build_context([SEG_1, SEG_2, SEG_3])
        assert len(ctx["segmentos"]) == 3
        assert ctx["num_total"] == 3

    def test_segmento_dict_keys(self):
        """Each segmento dict contains all expected keys."""
        ctx = build_context([SEG_1])
        s = ctx["segmentos"][0]
        expected_keys = {
            "v_origen", "v_destino", "x1", "y1", "x2", "y2",
            "distancia", "azimut", "rumbo", "orientacion",
            "colindancia_ref", "colindancia_poseedor", "tipo_colindancia",
            "colindancia_display",
        }
        assert expected_keys.issubset(s.keys())

    def test_colindancia_none_becomes_via_publica(self):
        """colindancia=None → colindancia_display='Vía pública'."""
        ctx = build_context([SEG_2])  # SEG_2 has colindancia=None
        s = ctx["segmentos"][0]
        assert s["colindancia_display"] == "Vía pública"

    def test_colindancia_present(self):
        """colindancia=string → colindancia_display returns the name."""
        ctx = build_context([SEG_1])
        s = ctx["segmentos"][0]
        assert s["colindancia_display"] == "Juan Pérez"

    def test_superficie_included(self):
        """superficie from polygon_attributes is present."""
        ctx = build_context([SEG_1], polygon_attributes={"superficie": 10000.0})
        assert ctx["superficie"] == 10000.0

    def test_perimetro_sum(self):
        """perimetro is sum of all segment distances."""
        ctx = build_context([SEG_1, SEG_2, SEG_3])
        assert ctx["perimetro"] == pytest.approx(300.0)

    def test_referencia_catastral(self):
        """referencia_catastral passed through."""
        ctx = build_context(
            [SEG_1],
            polygon_attributes={"referencia_catastral": "12345678AA0001"},
        )
        assert ctx["referencia_catastral"] == "12345678AA0001"

    def test_unknown_locale_does_not_fail(self):
        """Unknown locale defaults gracefully (no crash)."""
        ctx = build_context([SEG_1, SEG_2], locale="de")
        assert len(ctx["segmentos"]) == 2

    def test_empty_segments(self):
        """Empty list gives num_total=0, perimetro=0."""
        ctx = build_context([])
        assert ctx["num_total"] == 0
        assert ctx["perimetro"] == 0.0
        assert ctx["segmentos"] == []

    def test_missing_superficie_defaults_to_zero(self):
        """No superficie in attributes → defaults to 0."""
        ctx = build_context([SEG_1])
        assert ctx["superficie"] == 0.0

    def test_missing_referencia_defaults_to_empty(self):
        """No referencia_catastral in attributes → empty string."""
        ctx = build_context([SEG_1])
        assert ctx["referencia_catastral"] == ""

    def test_segmento_colindancia_ref_and_poseedor(self):
        """colindancia splits into colindancia_ref and colindancia_poseedor."""
        ctx = build_context([SEG_3])  # colindancia="María López"
        s = ctx["segmentos"][0]
        assert s["colindancia_ref"] == "María López"
        assert s["colindancia_poseedor"] == "María López"
        assert s["tipo_colindancia"] == "particular"

    def test_segmento_colindancia_none_ref_and_poseedor(self):
        """colindancia=None → colindancia_ref is None."""
        ctx = build_context([SEG_2])
        s = ctx["segmentos"][0]
        assert s["colindancia_ref"] is None
        assert s["colindancia_poseedor"] is None
        assert s["tipo_colindancia"] == "via_publica"
