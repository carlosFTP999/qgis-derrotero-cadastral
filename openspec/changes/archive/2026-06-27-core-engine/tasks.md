# Tasks: Core Engine — Derrotero Catastral

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,900 (29 new files) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: Engine → PR 2: Colindancia+Template → PR 3: Pipeline+GUI+Plugin |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Base |
|------|------|-----------|------|
| 1 | Engine pure modules + tests | PR 1 | feature/tracker |
| 2 | Colindancia + Template + tests | PR 2 | PR 1 branch |
| 3 | Processing + GUI + Plugin wiring + tests | PR 3 | PR 2 branch |

## Phase 1: Infrastructure

- [x] 1.1 Create `pyproject.toml` — pytest 9.0 + ruff 0.15 config
- [x] 1.2 Create `src/derrotero_catastral/__init__.py` — classFactory()
- [x] 1.3 Create `src/derrotero_catastral/metadata.txt` — QGIS 3.40 metadata
- [x] 1.4 Create `src/derrotero_catastral/engine/__init__.py` + `engine/types.py`

## Phase 2: Engine (TDD)

- [x] 2.1 Write `tests/test_geometry.py` (NW order, winding, holes, collinear)
- [x] 2.2 Create `engine/geometry.py` — extract_vertices(), order_nw()
- [x] 2.3 Write `tests/test_bearing.py` (azimuth, quadrant, DMS, cardinal es/en)
- [x] 2.4 Create `engine/bearing.py` — compute_bearing(), to_dms(), to_quadrant(), to_cardinal()
- [x] 2.5 Write `tests/test_distance.py` (geodetic, precision, totals, zero-length)
- [x] 2.6 Create `engine/distance.py` — compute_distance() using QgsDistanceArea
- [x] 2.7 Verify all engine unit tests pass

## Phase 3: Colindancia + Template

- [x] 3.1 Create `engine/colindancia.py` — build_index(), find_colindancias()
- [x] 3.2 Write `tests/test_colindancia.py` — QgsSpatialIndex edge cases
- [x] 3.3 Create `template/__init__.py` + `template/environment.py`
- [x] 3.4 Create `template/filters.py` + `tests/test_filters.py`
- [x] 3.5 Create `template/variables.py` + `tests/test_variables.py`
- [x] 3.6 Create `template/blueprints/es.j2`, `co.j2`, `generic.j2`

## Phase 4: Pipeline + GUI + Plugin

- [x] 4.1 Create `processing/__init__.py` + `processing/pipeline.py`
- [x] 4.2 Create `gui/__init__.py` + `gui/dock.py` — layer/template combos, generate btn
- [x] 4.3 Create `gui/preview.py` — QPlainTextEdit preview + TXT export
- [x] 4.4 Create `resources/__init__.py` + `resources/icon.svg`
- [x] 4.5 Create `derrotero_catastral.py` — initGui(), unload(), dock registration (updated placeholder → full implementation)

## Phase 5: Verification

- [x] 5.1 `pytest` — all 145 tests pass
- [x] 5.2 `ruff check src/` — no violations
- [~] 5.3 Verify plugin loads in QGIS: `pb_tool deploy` test (requires QGIS GUI — manual verification only)
- [~] 5.4 E2E: select layer → generate derrotero → preview → export TXT (requires QGIS GUI — manual verification only)
