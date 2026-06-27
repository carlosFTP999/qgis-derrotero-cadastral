"""Tests for engine/colindancia.py — spatial index and edge detection."""

from typing import Any

import pytest
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsRectangle,
    QgsSpatialIndex,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QVariant

from derrotero_catastral.engine.colindancia import build_index, find_colindancias
from derrotero_catastral.engine.types import Colindancia


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_layer(polygons_with_owners: list[tuple[QgsGeometry, str]]) -> QgsVectorLayer:
    """Create an in-memory polygon layer from (geometry, owner_name) tuples."""
    layer = QgsVectorLayer("Polygon", "test_colindancias", "memory")
    pr = layer.dataProvider()
    pr.addAttributes([
        QgsField("fid", QVariant.Int),
        QgsField("owner", QVariant.String),
    ])
    layer.updateFields()
    for i, (geom, owner) in enumerate(polygons_with_owners):
        feat = QgsFeature(layer.fields())
        feat.setGeometry(geom)
        feat.setAttributes([i + 1, owner])
        pr.addFeature(feat)
    layer.updateExtents()
    return layer


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------


class TestBuildIndex:
    """build_index(layer) — QgsSpatialIndex construction."""

    def test_returns_qgsspatialindex(self):
        """Returns a QgsSpatialIndex instance."""
        layer = _make_layer([
            (QgsGeometry.fromRect(QgsRectangle(0, 0, 10, 10)), "A"),
        ])
        index = build_index(layer)
        assert isinstance(index, QgsSpatialIndex)

    def test_index_finds_feature_by_bbox(self):
        """Index built from a layer contains features queryable by bbox."""
        layer = _make_layer([
            (QgsGeometry.fromRect(QgsRectangle(10, 20, 30, 40)), "Centro"),
        ])
        index = build_index(layer)
        hits = index.intersects(QgsRectangle(15, 25, 25, 35))
        assert len(hits) == 1

    def test_empty_layer_returns_empty_index(self):
        """Empty layer produces a valid but empty index."""
        layer = QgsVectorLayer("Polygon", "empty", "memory")
        layer.dataProvider().addAttributes([
            QgsField("fid", QVariant.Int),
            QgsField("owner", QVariant.String),
        ])
        layer.updateFields()
        layer.updateExtents()
        index = build_index(layer)
        assert isinstance(index, QgsSpatialIndex)
        # Query anything — should return empty
        hits = index.intersects(QgsRectangle(0, 0, 100, 100))
        assert len(hits) == 0


# ---------------------------------------------------------------------------
# find_colindancias
# ---------------------------------------------------------------------------


class TestFindColindancias:
    """find_colindancias() — edge-intersection detection."""

    @pytest.fixture
    def two_adjacent_squares(self) -> QgsVectorLayer:
        """Neighbour layer: only the adjacent parcel (B), not the source (A)."""
        return _make_layer([
            (QgsGeometry.fromRect(QgsRectangle(10, 0, 20, 10)), "Parcela B"),
        ])

    # --- R-CD-02: exact edge match ---------------------------------------

    def test_exact_edge_match(self, two_adjacent_squares: QgsVectorLayer):
        """Segment matching a shared edge returns the adjoining parcel."""
        layer = two_adjacent_squares
        index = build_index(layer)
        results = find_colindancias(
            segment_idx=0,
            segment=(10.0, 0.0, 10.0, 10.0),
            index=index,
            layer=layer,
        )
        assert len(results) == 1
        col = results[0]
        assert col.segment_idx == 0
        assert col.neighbor_owner == "Parcela B"
        assert col.overlap_length == pytest.approx(10.0, abs=0.01)

    # --- R-CD-04: open face ----------------------------------------------

    def test_no_match_returns_empty(self, two_adjacent_squares: QgsVectorLayer):
        """Segment far from all neighbours returns an empty list."""
        layer = two_adjacent_squares
        index = build_index(layer)
        results = find_colindancias(
            segment_idx=1,
            segment=(100.0, 100.0, 110.0, 110.0),
            index=index,
            layer=layer,
        )
        assert results == []

    # --- R-CD-03: multiple neighbours ------------------------------------

    def test_partial_colindancia_two_neighbors(self):
        """Segment crossing two stacked neighbours returns two colindancias."""
        # Source is left of x=10; neighbours B (lower) and C (upper) to the right
        layer = _make_layer([
            (QgsGeometry.fromRect(QgsRectangle(10, 0, 20, 10)), "B"),
            (QgsGeometry.fromRect(QgsRectangle(10, 10, 20, 20)), "C"),
        ])
        index = build_index(layer)
        results = find_colindancias(
            segment_idx=2,
            segment=(10.0, 0.0, 10.0, 20.0),
            index=index,
            layer=layer,
        )
        assert len(results) == 2
        owners = {r.neighbor_owner for r in results}
        assert "B" in owners
        assert "C" in owners
        for r in results:
            assert r.overlap_length == pytest.approx(10.0, abs=0.01)
            assert r.segment_idx == 2

    # --- R-CD-02: corner touching excluded -------------------------------

    def test_corner_touch_excluded(self):
        """Point-only intersection at a corner is NOT a colindancia."""
        # Source is left of x=10; B touches at corner (10,10) only
        layer = _make_layer([
            (QgsGeometry.fromRect(QgsRectangle(10, 10, 20, 20)), "B"),
        ])
        index = build_index(layer)
        results = find_colindancias(
            segment_idx=0,
            segment=(10.0, 0.0, 10.0, 10.0),
            index=index,
            layer=layer,
        )
        assert len(results) == 0

    # --- EV-01: empty layer ----------------------------------------------

    def test_empty_layer_graceful(self):
        """Empty neighbour layer returns empty colindancias gracefully."""
        layer = QgsVectorLayer("Polygon", "empty", "memory")
        layer.dataProvider().addAttributes([
            QgsField("fid", QVariant.Int),
            QgsField("owner", QVariant.String),
        ])
        layer.updateFields()
        layer.updateExtents()
        index = build_index(layer)
        results = find_colindancias(
            segment_idx=0,
            segment=(10.0, 0.0, 10.0, 10.0),
            index=index,
            layer=layer,
        )
        assert results == []
