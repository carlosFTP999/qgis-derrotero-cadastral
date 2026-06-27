# Vertex Extraction Specification

## Purpose

Vertex extraction is the initial stage of the derrotero generation pipeline. It reads a polygon geometry (with optional holes) and produces an ordered list of line segments representing the perimeter, starting from the northwesternmost point.

## Requirements

### R-VX-01: NW Origin

The extraction MUST start from the vertex with the maximum Y (northing) coordinate, breaking ties by selecting the minimum X (easting).

#### Scenario: Simple rectangle without ties
- GIVEN a rectangle with vertices (0,100)-(100,100)-(100,0)-(0,0)
- WHEN the NW origin is selected
- THEN the starting vertex is (0,100)

#### Scenario: Tie-breaking for equal Y values
- GIVEN a rectangle with vertices (10,100)-(20,100)-(20,0)-(10,0)
- WHEN the NW origin is selected
- THEN the starting vertex is (10,100)

### R-VX-02: Full perimeter ordering

The extracted vertices MUST traverse the entire perimeter in order, starting from NW. The final segment connects the last vertex back to the first.

#### Scenario: Square traversal
- GIVEN 4 unique perimeter vertices sorted NW-first
- WHEN the perimeter is extracted
- THEN 4 line segments are returned, forming a closed loop

### R-VX-03: Winding direction detection

The extraction MUST report whether the vertices run clockwise or counter-clockwise. PyQGIS's `QgsPolygon.isPolygonClockwise()` SHALL be used.

#### Scenario: clockwise polygon
- GIVEN a polygon with vertices in clockwise order
- WHEN winding is detected
- THEN the direction SHALL be reported as CLOCKWISE

### R-VX-04: Interior ring handling

Anticyclonic interior rings (holes) MUST each be extracted as an independent closed ring. Holes have their own NW origin and winding.

#### Scenario: Polygon with one hole
- GIVEN a polygon with one interior ring (hole)
- WHEN holes are extracted
- THEN the hole is returned as separate perimeter with its own vertex list

### R-VX-05: Collinear vertex deduplication

The extraction SHOULD remove collinear vertices using `QgsGeometry.removeDuplicateNodes()`. This is configurable.

#### Scenario: Collinear removal enabled
- GIVEN a quad strip with a redundant collinear intermediate vertex
- WHEN collinear removal is enabled
- THEN the collinear vertex is omitted
- AND the segment count is reduced accordingly

#### Scenario: Collinear removal disabled
- GIVEN the same quad strip
- WHEN collinear removal is disabled
- THEN ALL original vertices are included

### R-VS-01: Curved segment conversion

Curved segments (arcs) MUST be linearized via `QgsCurve.convertToStraightSegment()`. A default segments-per-curve value SHALL be used.

#### Scenario: Circular arc
- GIVEN a polygon with one curved segment
- WHEN the curve is linearized
- THEN the curve is replaced by straight segments approximating its shape

### EV-01: Insufficient geometry

If the polygon has fewer than 3 vertices after processing, extraction MUST raise an error.

#### Scenario: degenerate triangle
- GIVEN a geometry with only 2 distinct vertices
- WHEN extraction is attempted
- THEN an error is raised

### EV-02: Null geometry

If the layer feature has no geometry, extraction MUST return None silently, allowing the next iteration to proceed.

#### Scenario: feature with no geometry
- GIVEN a feature whose geometry is NULL
- WHEN extraction is attempted
- THEN None is returned without error
