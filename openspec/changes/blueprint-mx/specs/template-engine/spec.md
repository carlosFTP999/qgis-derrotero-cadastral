# Delta for Template Engine

## ADDED Requirements

### R-TE-06: Mexican blueprint (mx.j2)

The built-in set MUST include an `mx` blueprint (mx.j2) for Mexican "Acta de Colindancia" format. It SHALL render sexagesimal rumbo via `to_quadrant(azimut, dms=True)`, 2-decimal distances, and `es` locale cardinal directions (identical to Mexican usage). It SHALL produce plain text output, not Markdown.

#### Scenario: 4-sided parcel renders correctly

- GIVEN `segmentos` with 4 segments, each with computed rumbo and colindancia
- WHEN the `mx.j2` blueprint is rendered
- THEN output SHALL contain a header with "ACTA DE COLINDANCIA" and the reference catastral
- AND each segment SHALL appear as a "LINDERO" block with rumbo (sexagesimal) and 2-decimal distance
- AND the footer SHALL show superficie and perímetro with 2-decimal precision

#### Scenario: open face colindancia renders as "Vía pública"

- GIVEN a segment with `colindancia: None`
- WHEN rendered as `s.colindancia_display`
- THEN the colindancia field SHALL read "Vía pública"

#### Scenario: edge case — zero-area parcel

- GIVEN a single-segment polygon (superficie = 0.0, perimetro = 0.0)
- WHEN rendered
- THEN output SHALL show 0.00 for both superficie and perímetro
- AND the single lindero SHALL render correctly

#### Scenario: cardinal direction shortcuts

- GIVEN a segment with azimuth exactly 0.0, 90.0, 180.0, or 270.0
- WHEN converted via `to_quadrant(dms=True)`
- THEN the rumbo SHALL be a single cardinal letter (N, E, S, W) with no angle
