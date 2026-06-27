# Derrotero Catastral

**QGIS plugin for generating cadastral traverse (derrotero) documents from parcel polygons.**

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
![QGIS](https://img.shields.io/badge/QGIS-3.28%E2%80%933.99-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/Tests-145%20passing-brightgreen)

---

## Overview

Derrotero Catastral automates the generation of **derroteros catastrales** — structured documents that describe a parcel's perimeter vertex by vertex with bearings, distances, and adjoining property (colindancia) information. The plugin reads a polygon layer, extracts the perimeter geometry, computes geodetic measurements, and renders the result through customisable Jinja2 templates.

This saves surveyors, land registrars, and cadastral technicians hours of manual drafting.

---

## Features

- **Vertex extraction** — extract ordered perimeter vertices from polygon geometries, with Northwest-start ordering (NW → NE → SE → SW), collinear vertex removal, and curve linearisation.
- **Bearing & distance** — forward azimuth (0–360°), quadrant bearing (e.g. *N 45° E*), cardinal orientation (e.g. *Noreste*), and geodetic distance via QgsDistanceArea (ellipsoidal).
- **Colindancia detection** — automatic identification of adjoining parcels using QgsSpatialIndex with per-segment edge matching.
- **Template engine** — sandboxed Jinja2 environment with custom filters (`to_dms`, `to_quadrant`, `to_cardinal`, `format_number`) and multi-locale support.
- **Multiple blueprints** — built-in templates for Spanish (`es.j2`), Colombian LADM-COL (`co.j2`), and tabular (`generic.j2`) output.
- **Dock widget UI** — polygon layer selection, feature picker, optional colindancia layer, template selector, live preview, and TXT export.
- **QSettings persistence** — remembers the last layer, template, and dock geometry across sessions.

---

## Requirements

| Dependency | Version |
|------------|---------|
| QGIS | 3.28 – 3.99 |
| Python | ≥ 3.10 |
| PyQt5 | ≥ 5.15 |
| Jinja2 | ≥ 3.0 (bundled with QGIS) |

The plugin uses only QGIS-bundled dependencies. No external PyPI packages are required.

---

## Installation

### Option 1 — pb_tool (recommended for development)

```bash
pb_tool deploy
```

### Option 2 — manual

1. Create a `DerroteroCatastral` directory inside your QGIS `profiles/default/python/plugins/` folder.
2. Copy the contents of `src/derrotero_catastral/` into it.
3. Restart QGIS and enable the plugin via **Plugins → Manage and Install Plugins**.

### Option 3 — zip deployment

```bash
cd src
zip -r derrotero-catastral.zip derrotero_catastral/
```

Then install via **Plugins → Manage and Install Plugins → Install from ZIP**.

---

## Usage

1. **Load a polygon layer** — any vector layer with polygon geometry (Shapefile, GeoPackage, PostGIS, etc.).
2. **Open the dock** — via **View → Panels → Derrotero Catastral**, or click the toolbar icon.
3. **Select a parcel** — choose a feature from the *Predio* dropdown. The combo tries common display fields (*owner, nombre, name, parcela, label*) and falls back to *FID {N}*.
4. **(Optional) Select a colindancia layer** — a second polygon layer with neighbouring parcels for automatic adjoining-property detection.
5. **Choose a template** — *es.j2* (Spanish text), *co.j2* (LADM-COL format), or *generic.j2* (table).
6. **Click *Generar Derrotero*** — the rendered document appears in the preview area.
7. **Export** — click *Exportar TXT* to save the result as a plain-text file.

### Adding custom templates

Place `.j2` files in the user templates directory:

| OS | Path |
|----|------|
| Linux | `~/.local/share/QGIS/QGIS3/profiles/default/derrotero/templates/` |
| Windows | `%APPDATA%\QGIS\QGIS3\profiles\default\derrotero\templates\` |
| macOS | `~/Library/Application Support/QGIS/QGIS3/profiles/default/derrotero/templates/` |

User templates override built-in ones with the same filename. Templates have access to the `segmentos` context variable and custom filters (`format_number`, `to_dms`, `to_quadrant`, `to_cardinal`).

---

## Architecture

```
                     ┌─────────────────────────────────┐
                     │      DerroteroCatastralPlugin    │
                     │  (initGui / unload / lifecycle)  │
                     └────────────┬────────────────────┘
                                  │ owns
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
   ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │  DerroteroDock  │  │    Preview       │  │ PipelineOrch.   │
   │  (layer/tpl     │─▶│  (QPlainTextEdit)│  │ (engine→tpl→out)│
   │   selection)    │  │  read-only       │  └────────┬─────────┘
   └─────────────────┘  └──────────────────┘           │
                                                        │ uses
                    ┌───────────────────────────────────┤
                    ▼                                   ▼
          ┌──────────────────┐                ┌──────────────────┐
          │  Engine Layer    │                │  Template Layer  │
          │  geometry.py     │                │  environment.py  │
          │  bearing.py      │                │  filters.py      │
          │  distance.py     │                │  variables.py    │
          │  colindancia.py  │                │  blueprints/*.j2 │
          │  types.py        │                └──────────────────┘
          └──────────────────┘
```

### Layers

| Layer | Responsibility |
|-------|---------------|
| **engine** | Pure domain logic: geometry extraction, bearing/distance computation, colindancia detection. Fully unit-tested. |
| **template** | Jinja2 sandboxed environment, custom filters, context builder, and blueprint files. |
| **processing** | `PipelineOrchestrator` — coordinates the full 8-step flow from feature geometry to rendered text. |
| **gui** | `DerroteroDock` (Qt dock widget), `DerroteroPreview` (read-only text preview). |

### Engine modules

| Module | Key functions |
|--------|--------------|
| `geometry.py` | `extract_vertices()`, `order_nw()`, `remove_collinear()`, `linearize_curve()`, `extract_interior_rings()` |
| `bearing.py` | `compute_azimuth()`, `normalize_azimuth()`, `to_quadrant_bearing()`, `to_dms()`, `to_cardinal()` |
| `distance.py` | `compute_distance()`, `round_distance()`, `compute_totals()` |
| `colindancia.py` | `build_index()`, `find_colindancias()` |
| `types.py` | `Vertex`, `SegmentData`, `Colindancia` — all `NamedTuple`-based DTOs |

---

## Blueprints

| File | Locale | Format | Use case |
|------|--------|--------|----------|
| `es.j2` | es | Narrative text | Standard Spanish derrotero with natural-language phrasing |
| `co.j2` | co | Structured fields | Colombian LADM-COL format with colindante reference/poseedor |
| `generic.j2` | — | Markdown table | Tabular output with all computed fields |

Blueprints use a sandboxed Jinja2 environment with a restricted builtins whitelist (`range`, `dict`, `str`, `int`, `float`, `bool`, `enumerate`, `zip`, `len`).

---

## Development

### Setting up

```bash
# Clone the repository
git clone https://github.com/placeholder/derrotero-catastral.git
cd derrotero-catastral

# Install development tools
pip install pytest pytest-cov ruff pb_tool qgis-manage

# Run tests (standalone, no QGIS GUI needed)
python -m pytest tests/ -v
```

### Running tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/derrotero_catastral/engine

# Specific module
pytest tests/test_bearing.py -v
```

All 145 tests run without a QGIS GUI — they use `pytest-qgis` headless mocking.

### Code style

```bash
ruff check src/
ruff format src/ --check
```

The project uses Ruff with `target-version = "py310"`, `line-length = 100`, and double quotes.

---

## Roadmap

### v0.1.0 (current) — Core engine
- [x] Vertex extraction and NW ordering
- [x] Azimuth and quadrant bearing computation
- [x] Geodetic distance calculation
- [x] Colindancia detection with spatial index
- [x] Sandboxed Jinja2 template engine
- [x] Three built-in blueprints (es, co, generic)
- [x] Pipeline orchestrator
- [x] Dock widget with preview and TXT export
- [x] 145 unit tests

### v0.2.0 (planned)
- [ ] PDF export (via ReportLab or WeasyPrint)
- [ ] DOCX export (via python-docx)
- [ ] Batch processing for multiple parcels

### v0.3.0 (planned)
- [ ] Configurable symbology for selected parcels
- [ ] In-canvas vertex labels
- [ ] i18n translations (.qm files)
- [ ] Mexican (mx) and Chilean (cl) blueprint variants

---

## License

**GNU General Public License v3.0 or later** — see [LICENSE](LICENSE).

This is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation.
