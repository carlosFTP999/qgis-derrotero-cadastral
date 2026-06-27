# Distance Calculation Specification

## Purpose

Calculate the geodetic distance between each vertex pair in the extracted perimeter and maintain cumulative totals for parcel dimensions.

## Requirements

### R-DC-01: Geodetic distance

The system MUST compute the distance between two points using QgsDistanceArea. The measureLine method SHALL be used with the project's ellipsoidal CRS. The result MUST be meters.

#### Scenario: Simple geodetic distance
- GIVEN two geographic coordinates separated by ~100m
- WHEN distance is computed
- THEN the result SHALL be in meters and match expected geodetic distance.

### R-DC-02: CRS configuration

The calculator SHALL be configured with the project's source CRS. Elipsoidal vs. planar calculation SHALL be toggleable via a boolean flag.

#### Scenario: Planar mode
- GIVEN planar mode is enabled
- WHEN distance is calculated
- THEN the measurement is performed without ellipsoidal correction

### R-DC-03: Configurable precision

Distance output SHALL be rounded to a configurable number of decimal places. Default is 3 (mm precision).

#### Scenario: Default precision
- GIVEN a computed distance of 100.12345 m
- WHEN rounding with default precision
- THEN the result SHALL be 100.123

#### Scenario: Custom precision
- GIVEN a computed distance of 100.12345 m
- WHEN rounding with precision 0
- THEN the result SHALL be 100.0

### R-DC-04: Cumulative totals

The system MUST maintain a running total of all segment raw distances. Total distance is the sum of raw values, rounded once as a final step.

#### Scenario: Segment sum
- GIVEN two consecutive segments 10.123 m and 20.456 m
- WHEN total distance is computed
- THEN the grand total SHALL be 30.579

### EV-01: zero-length segment

- GIVEN source and target are identical
- WHEN distance is computed
- THEN the result SHALL be 0.0

### EV-02: negative precision

If a negative value is passed for precision, the system SHOULD fall back to the default (3).
