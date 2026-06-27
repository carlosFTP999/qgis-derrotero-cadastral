# Bearing Calculation Specification

## Purpose

Calculate azimuth (0-360° from North), quadrant bearing (DMS format), and cardinal orientation for each segment of a parcel polygon.

## Requirements

### Requirement: Azimuth

The system MUST compute the forward azimuth from vertex A to vertex B using `QgsPointXY.azimuth()`.

The raw result (-180 to 180 degrees from North, clockwise) MUST be normalized to the range [0, 360).

| Input points | Raw azimuth | Normalized |
|---|---|---|
| A(0,0) → B(1,1) | 45.0 | 45.0 |
| A(0,0) → B(1,-1) | -45.0 | 315.0 |
| A(0,0) → B(-1,1) | 135.0 | 135.0 |
| A(0,0) → B(-1,-1) | -135.0 | 225.0 |

#### Scenario: Normalized azimuth from North

- GIVEN points A(0,0) and B(0,1)
- WHEN azimuth is computed
- THEN the result SHALL be 0.0 (due North)

#### Scenario: Negative azimuth normalized

- GIVEN points A(0,0) and B(1,-1)
- WHEN azimuth is computed and normalized
- THEN the result MUST be 315.0

### Requirement: Quadrant Bearing (Rumbo)

The system MUST convert a normalized azimuth to quadrant bearing format: `{N|S} θ° {E|W}`.

| Azimuth range | Quadrant | Formula |
|---|---|---|
| 0-90° | N θ E | θ = azimuth |
| 90-180° | S θ E | θ = 180 - azimuth |
| 180-270° | S θ W | θ = azimuth - 180 |
| 270-360° | N θ W | θ = 360 - azimuth |

#### Scenario: Bearing in NE quadrant

- GIVEN an azimuth of 45.0°
- WHEN converted to quadrant bearing
- THEN the result MUST be "N 45° E"

#### Scenario: Bearing in SW quadrant

- GIVEN an azimuth of 225.0°
- WHEN converted to quadrant bearing
- THEN the result MUST be "S 45° W"

### Requirement: DMS Format

The rumbo SHOULD support degrees-minutes-seconds format: `{N|S} θ° m' s" {E|W}`.

The precision of seconds MUST be configurable (default: 1 decimal place).

#### Scenario: DMS with remainder

- GIVEN an azimuth of 45.5°
- WHEN converted to DMS quadrant bearing
- THEN the result SHALL be "N 45° 30' 0.0\" E"

### Requirement: Cardinal Orientation

The system MUST map azimuth to one of 8 cardinal directions.

| Azimuth range | Orientation |
|---|---|
| 337.5 - 22.5 | Norte |
| 22.5 - 67.5 | Noreste |
| 67.5 - 112.5 | Este |
| 112.5 - 157.5 | Sureste |
| 157.5 - 202.5 | Sur |
| 202.5 - 247.5 | Suroeste |
| 247.5 - 292.5 | Oeste |
| 292.5 - 337.5 | Noroeste |

#### Scenario: Edge of range

- GIVEN azimuth of 337.5°
- WHEN mapped to cardinal
- THEN the result MUST be "Norte"

#### Scenario: Exact cardinal midpoint

- GIVEN azimuth of 90.0°
- WHEN mapped to cardinal
- THEN the result MUST be "Este"

### Requirement: Locale Support

The cardinal orientation and bearing labels SHOULD support multiple locales. The default locale SHOULD be `es` (Spanish).

The system MUST provide at minimum: `es` (español), `en` (English).

## Edge Cases

### Requirement: Zero-length segment

- GIVEN a segment where A and B are the same point
- WHEN azimuth is computed
- THEN the result MUST raise or return a sentinel value (None / NaN)

### Requirement: Due cardinal points

- GIVEN azimuth values exactly 0°, 90°, 180°, 270°
- WHEN quadrant bearing is computed
- THEN edge azimuths at 0° and 180° MUST produce "N" and "S" without E/W suffix
- AND edge azimuths at 90° and 270° MUST produce "E" and "W" without N/S prefix
