# Tasks: Blueprint MX

## Change Summary

Add a Mexican cadastral blueprint (`mx.j2`) to the Derrotero Catastral QGIS plugin. Single file, zero Python code changes, auto-discovered by the existing blueprint scanner.

## Delivery Forecast

- **Decision needed before apply**: No
- **Chained PRs recommended**: No
- **400-line budget risk**: Low (~30 lines total)

## Tasks

### T1: Create mx.j2 blueprint file

**Scope**: New file — `src/derrotero_catastral/template/blueprints/mx.j2`

Create the Mexican Acta de Colindancia template:

- Render header with "ACTA DE COLINDANCIA" and reference catastral
- Loop over `segmentos` and render each as a "LINDERO" block:
  - Vertex range (V1 → V2)
  - Sexagesimal rumbo via `to_quadrant(azimut, dms=True)`
  - 2-decimal distance via `"%.2f"|format(s.distancia)`
  - Colindancia display via `s.colindancia_display`
- Footer with superficie and perímetro (2 decimals)

**Acceptance**: See spec scenarios in `specs/template-engine/spec.md`.

### T2: Verify mx.j2 renders correctly

**Scope**: Manual or automated rendering check.

- Load a 4-sided parcel in QGIS
- Generate derrotero selecting the "mx.j2" blueprint from the combo
- Verify:
  - Output matches expected format (Acta de Colindancia)
  - Rumbo is sexagesimal with DMS notation
  - Distances have 2 decimal places
  - Open-face colindancias display as "Vía pública"
  - Surface and perimeter appear in the footer
- Alternatively: write a unit test using the existing `render_blueprint` test helper (if available) that instantiates the environment and renders `mx.j2` with mock segment data
