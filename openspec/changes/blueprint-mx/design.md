# Blueprint MX — Technical Design

## Overview

Add `mx.j2` to the built-in blueprints directory. Zero Python code changes — the file scan in `dock.py` auto-discovers new `.j2` files.

## Template

**File**: `src/derrotero_catastral/template/blueprints/mx.j2`

```jinja2
============================================================
                     ACTA DE COLINDANCIA
============================================================
Referencia Catastral: {{ referencia_catastral }}

------------------------------------------------------------
                         LINDEROS
------------------------------------------------------------
{% for s in segmentos %}
LINDERO {{ loop.index }}
  Del vértice V{{ s.v_origen + 1 }} al vértice V{{ s.v_destino + 1 }}
  Rumbo: {{ s.azimut|to_quadrant(dms=True) }}
  Distancia: {{ "%.2f"|format(s.distancia) }} m
  Colindancia: {{ s.colindancia_display }}

{% endfor %}
============================================================
                     DATOS DEL PREDIO
============================================================
  Superficie: {{ "%.2f"|format(superficie) }} m²
  Perímetro: {{ "%.2f"|format(perimetro) }} m
```

## Template Variables Used

| Variable | Type | Source |
|----------|------|--------|
| `segmentos` | list[dict] | `variables.py` — one dict per segment |
| `s.v_origen`, `s.v_destino` | int | 0-based vertex indices |
| `s.azimut` | float | Degrees, usable as filter input |
| `s.distancia` | float | Meters |
| `s.colindancia_display` | str | None → "Vía pública" |
| `superficie` | float | Square meters |
| `perimetro` | float | Meters |
| `referencia_catastral` | str | Parcel reference code |

## Custom Filters Used

| Filter | Invocation | Output Example |
|--------|-----------|---------------|
| `to_quadrant(dms=True)` | `s.azimut\|to_quadrant(dms=True)` | `N 45° 30' 0.0" E` |
| `format` (Jinja2 built-in) | `"%.2f"\|format(s.distancia)` | `100.00` |

## Design Decisions

1. **`es` locale** for cardinal directions — identical to Mexican usage, no separate locale needed.
2. **`to_quadrant(dms=True)`** for sexagesimal rumbo — required by Mexican cadastral standards.
3. **`colindancia_display`** over raw `colindancia` — automatically handles None→"Vía pública" for open faces.
4. **No new filters or dependencies** — reuses everything already in the sandboxed environment.

## Example Output (4-sided parcel)

```
============================================================
                     ACTA DE COLINDANCIA
============================================================
Referencia Catastral: MX-1234-5678-90

------------------------------------------------------------
                         LINDEROS
------------------------------------------------------------

LINDERO 1
  Del vértice V1 al vértice V2
  Rumbo: N 45° 30' 0.0" E
  Distancia: 100.00 m
  Colindancia: Vía pública

LINDERO 2
  Del vértice V2 al vértice V3
  Rumbo: S 44° 30' 0.0" E
  Distancia: 50.00 m
  Colindancia: Juan Pérez López

LINDERO 3
  Del vértice V3 al vértice V4
  Rumbo: S 45° 30' 0.0" O
  Distancia: 100.00 m
  Colindancia: Vía pública

LINDERO 4
  Del vértice V4 al vértice V1
  Rumbo: N 44° 30' 0.0" O
  Distancia: 50.00 m
  Colindancia: María García Hernández

============================================================
                     DATOS DEL PREDIO
============================================================
  Superficie: 5000.00 m²
  Perímetro: 300.00 m
```
