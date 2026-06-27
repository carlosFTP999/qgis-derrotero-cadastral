# Proposal: Core Engine — Derrotero Catastral

## Intent

First implementation of the Derrotero Catastral QGIS plugin. Provide a modular core engine that extracts parcel vertices ordered from NW, calculates geodetic bearings and distances, detects adjoining parcels (colindancias) via spatial index, and generates derrotero text through customizable Jinja2 templates.

## Scope

### In Scope
- Geometry engine: vertex extraction, NW ordering, winding detection
- Bearing/distance: azimuth (0-360°), quadrant bearing (DMS), cardinal orientation
- Colindancia detection: spatial index, per-segment intersection, multi-owner support
- Template engine: Jinja2 SandboxedEnvironment with custom filters
- TXT output: plain-text derrotero from built-in blueprints (ES, COL, MX, generic)
- Dock widget UI: layer selection, template chooser, generate & preview
- Installable plugin package (pb_tool)

### Out of Scope
- PDF export (v2)
- DOCX export (v2)
- Map visualization / highlight
- Batch/multi-parcel processing
- CRS reprojection UI

## Capabilities

### New Capabilities
- `vertex-extraction`: Ordered vertex extraction from NW origin, polygon winding detection
- `bearing-calculation`: Azimuth (0-360°), quadrant bearing with configurable DMS, cardinal orientation
- `distance-calculation`: Geodetic distance via QgsDistanceArea
- `colindancia-detection`: Per-segment colindancia using QgsSpatialIndex + intersection
- `template-engine`: Jinja2 SandboxedEnvironment, custom filters (to_dms, to_quadrant, format_number), multi-locale DSL variables
- `derrotero-generation`: TXT rendering from templates, built-in blueprints, user template folder

### Modified Capabilities
None — initial implementation.

## Approach

Layered architecture: `engine/` (pure geometry/trig, no Qt) → `templates/` (Jinja2) → `processing/` (QGIS algorithms) → `gui/` (dock widget). Each layer depends only on the one below it. Processing layer bridges QGIS types ↔ engine DTOs.

## Affected Areas

All areas are **New** (empty project):

| Area | Impact | Description |
|------|--------|-------------|
| `src/derrotero/engine/` | New | Vertex extraction, bearing, distance |
| `src/derrotero/engine/colindancia.py` | New | Spatial index colindancia detection |
| `src/derrotero/templates/` | New | Jinja2 environment, filters, blueprints |
| `src/derrotero/processing/` | New | QgsProject → engine DTOs |
| `src/derrotero/gui/` | New | Dock widget, template selector |
| `src/derrotero/resources/` | New | Icons, built-in templates |
| `tests/` | New | Unit + integration tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Performance with large adjacent layers | Medium | QgsSpatialIndex + limit search radius |
| CRS mismatch between parcel and colindancias | Medium | Validate CRS, reproject on the fly |
| Jinja2 sandbox escape | Low | SandboxedEnvironment + restricted builtins |
| Jinja2 not bundled with QGIS Python | Low | Bundle pure-Python Jinja2 in plugin |

## Rollback Plan

Remove plugin directory from `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/derrotero/` and restart QGIS. No user data is created or modified outside the plugin folder.

## Dependencies

- Jinja2 3.1.6 (bundled in plugin, not system)
- QGIS 3.40.6+ (PyQGIS API)
- pytest 9.0.3 (dev only)

## Success Criteria

- [ ] Extract vertices ordered from NW for any polygon (including holes)
- [ ] Compute azimuth, quadrant bearing, and cardinal orientation correctly
- [ ] Detect colindancias via QgsSpatialIndex with per-segment accuracy
- [ ] Render derrotero TXT from a Jinja2 template with all DSL variables
- [ ] All unit tests pass under pytest
- [ ] Plugin installable and loadable via pb_tool
