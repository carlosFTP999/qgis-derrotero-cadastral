# Design: Core Engine — Derrotero Catastral

## Technical Approach

Layered architecture with strict dependency direction: `engine/` (pure Python) → `templates/` (Jinja2) → `processing/` (QGIS bridge) → `gui/` (Qt dock). Each layer depends only on the one below it. This enables unit-testing engine logic without a QGIS session and swapping the UI layer independently.

## Architecture Decisions

### Decision: Package name — `derrotero_catastral`

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `derrotero` | Shorter, but generic and may conflict with other plugins | ❌ |
| `derrotero_catastral` | Self-documenting, avoids namespace conflicts | ✅ |
| `qgis_derrotero` | Verbose | ❌ |

**Rationale**: QGIS plugin namespace is flat — `derrotero_catastral` uniquely identifies the plugin and is descriptive in Spanish (target audience).

### Decision: Engine DTOs — `NamedTuple` over QGIS types

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Pass `QgsPointXY` to templates | Ties Jinja2 to QGIS types, can't reuse templates offline | ❌ |
| `dataclass` + `asdict()` | Mutable, but engine produces immutable data | ❌ |
| `typing.NamedTuple` | Immutable, hashable, lightweight, `._asdict()` for Jinja2 | ✅ |

**Choice**: `SegmentData(NamedTuple)` with `v_origen`, `v_destino` (int), `x1`, `y1`, `x2`, `y2` (float), `distancia` (float), `azimut` (float), `rumbo` (str), `orientacion` (str), `colindancia` (Optional[str]).

**Rationale**: NamedTuples are zero-overhead, immutable by default, and `_asdict()` feeds Jinja2 context directly.

### Decision: SpatialIndex — cached per layer selection

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Rebuild QgsSpatialIndex per feature | Simple but O(n·m), slow with large layers | ❌ |
| Build once when colindancia layer loads | Fast, but stale if layer edits occur | ✅ |
| Build on demand with memoization | Balances freshness and perf | ❌ overengineering |

**Choice**: Build `QgsSpatialIndex` once when user selects or changes the colindancia layer. Store in the processing layer's orchestrator. User can re-index via a "refresh" button.

### Decision: Template loading — user path takes precedence

| Source | Path | Precedence |
|--------|------|------------|
| Built-in | `pkg_resources.files("derrotero_catastral") / "templates/blueprints"` | Fallback |
| User | `QStandardPaths.writableLocation(AppDataLocation) / "derrotero/templates"` | Override |

**Choice**: Two-dir `FileSystemLoader` chain — user first, built-in second. No hot-reload in v1 (engine restart required). No cache — Jinja2 caching is opt-in v2.

### Decision: Jinja2 — bundled pure-Python fallback

QGIS 3.40 ships Python 3.13 but may not include Jinja2. Strategy:

1. Try `import jinja2` (system/host Python)
2. Fallback: bundled `jinja2/` in plugin root (pure Python, no C extensions)
3. `SandboxedEnvironment(builtins=[])` with explicit whitelist: `range`, `dict`, `list`, `str`, `int`, `float`, `bool`, `True`, `False`, `None`, `enumerate`, `zip`, `len`

### Decision: Plugin lifecycle — dock widget via QSettings

Standard QGIS `initGui()`/`unload()` pattern. The dock widget is created once in `initGui()` and registered via `iface.addDockWidget()`. State (last layer, last template, window geometry) persists through `QSettings("derrotero_catastral", "derrotero_catastral")`.

## Data Flow

```
User selects layer + feature
       │
       ▼
processing/PipelineOrchestrator
       │
       ├── engine/geometry.py
       │   ├── extract_vertices(geom) → list[Vertex]
       │   └── order_nw(vertices) → list[Vertex] (NW start)
       │
       ├── engine/bearing.py
       │   └── compute_bearing(a, b) → (azimut, rumbo, orientacion)
       │
       ├── engine/distance.py
       │   └── compute_distance(a, b, crs) → metros
       │
       ├── engine/colindancia.py
       │   └── find_colindancias(segment, index, layer) → list[Colindancia]
       │
       ├── template/variables.py
       │   └── build_context(segments, attributes) → dict
       │
       └── template/environment.py
           └── render(template_name, context) → str
                    │
                    ▼
              gui/preview.py → QPlainTextEdit
                    │
                    ▼
              QFileDialog → TXT file
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/derrotero_catastral/__init__.py` | Create | `classFactory()` entry point per QGIS spec |
| `src/derrotero_catastral/derrotero_catastral.py` | Create | Plugin class: `initGui()`, `unload()`, dock registration |
| `src/derrotero_catastral/metadata.txt` | Create | QGIS plugin metadata (version, author, category) |
| `src/derrotero_catastral/engine/__init__.py` | Create | Package init |
| `src/derrotero_catastral/engine/geometry.py` | Create | Vertex extraction, NW ordering, winding, curve linearization |
| `src/derrotero_catastral/engine/bearing.py` | Create | Azimuth, quadrant bearing, DMS, cardinal, locale support |
| `src/derrotero_catastral/engine/distance.py` | Create | Geodetic distance via `QgsDistanceArea`, precision, totals |
| `src/derrotero_catastral/engine/colindancia.py` | Create | `QgsSpatialIndex` build + per-segment intersection detection |
| `src/derrotero_catastral/engine/types.py` | Create | `SegmentData`, `Vertex`, `Colindancia` NamedTuples |
| `src/derrotero_catastral/template/__init__.py` | Create | Package init |
| `src/derrotero_catastral/template/environment.py` | Create | `SandboxedEnvironment`, two-dir loader |
| `src/derrotero_catastral/template/filters.py` | Create | `to_dms`, `to_quadrant`, `format_number`, `to_cardinal` |
| `src/derrotero_catastral/template/variables.py` | Create | Context builder: segments + attributes → flat dict |
| `src/derrotero_catastral/template/blueprints/es.j2` | Create | Spanish classic blueprint |
| `src/derrotero_catastral/template/blueprints/co.j2` | Create | Colombia LADM-COL blueprint |
| `src/derrotero_catastral/template/blueprints/generic.j2` | Create | Compact table blueprint |
| `src/derrotero_catastral/processing/__init__.py` | Create | Package init |
| `src/derrotero_catastral/processing/pipeline.py` | Create | `PipelineOrchestrator`: coordinates engine → template |
| `src/derrotero_catastral/gui/__init__.py` | Create | Package init |
| `src/derrotero_catastral/gui/dock.py` | Create | QDockWidget: layer combo, template combo, generate btn |
| `src/derrotero_catastral/gui/preview.py` | Create | QPlainTextEdit read-only preview + export btn |
| `src/derrotero_catastral/resources/__init__.py` | Create | Package init (empty) |
| `src/derrotero_catastral/resources/icon.svg` | Create | Plugin icon |
| `tests/__init__.py` | Create | Test package |
| `tests/test_geometry.py` | Create | Unit tests: NW ordering, winding, linearization |
| `tests/test_bearing.py` | Create | Unit tests: azimuth, quadrant, DMS, cardinal, locales |
| `tests/test_distance.py` | Create | Unit tests: geodetic distance, precision, totals |
| `tests/test_colindancia.py` | Create | Unit tests: spatial index, intersection edge cases |
| `tests/test_filters.py` | Create | Unit tests: Jinja2 custom filters |
| `tests/test_variables.py` | Create | Unit tests: context building |
| `pyproject.toml` | Create | Pytest config, ruff config, project metadata |

## Interfaces / Contracts

```python
# src/derrotero_catastral/engine/types.py

from typing import NamedTuple, Optional

class Vertex(NamedTuple):
    index: int
    x: float
    y: float

class SegmentData(NamedTuple):
    v_origen: int
    v_destino: int
    x1: float
    y1: float
    x2: float
    y2: float
    distancia: float
    azimut: float
    rumbo: str
    orientacion: str
    colindancia: Optional[str]  # owner name or None

    @property
    def length_m(self) -> str:
        return f"{self.distancia:.3f}"

class Colindancia(NamedTuple):
    segment_idx: int
    neighbor_fid: int
    neighbor_owner: Optional[str]
    overlap_length: float
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | `engine/geometry.py` — vertex extraction, NW ordering | Pure Python, no QGIS needed. pytest parametrize over rectangle/square/hole fixtures |
| Unit | `engine/bearing.py` — azimuth normalization, quadrant, DMS, cardinal | Table-driven: 30+ cases covering quadrants, edges, cardinal boundaries |
| Unit | `engine/distance.py` — precision, totals, zero-length | Mock `QgsDistanceArea` via pytest-monkeypatch |
| Unit | `template/filters.py` — to_dms, to_quadrant, format_number | Pure Jinja2 test environment, no QGIS |
| Unit | `template/variables.py` — context assembly | Verify dict keys match template expectations |
| Integration | `engine/colindancia.py` | Requires `QgsGeometry` but not GUI — use `QgsApplication` headless or pytest-qgis |
| Integration | `processing/pipeline.py` | End-to-end with realistic geometries |

**Note**: pytest-qgis is NOT installed. Colindancia tests use `QgsGeometry` directly (available in QGIS Python) without QGIS GUI. Pipeline integration tests run inside QGIS Python if possible, or are deferred until pytest-qgis is available.

## Migration / Rollout

No migration required. This is the initial plugin implementation. Rollout is manual: `pb_tool deploy` or copy plugin directory to QGIS profiles.

## Open Questions

- [ ] Confirm whether the user wants to bundle Jinja2 as a fallback zip or as an extracted directory inside the plugin
- [ ] Confirm locale list for cardinal/bearing labels: `es`, `en` confirmed; are `co` (Colombia) or `mx` (Mexico) needed at v1?
- [ ] Verify whether `QgsApplication` headless initialization works in the test runner for colindancia tests without pytest-qgis
