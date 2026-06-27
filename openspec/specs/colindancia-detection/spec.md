# Colindancia Detection Specification

## Purpose

For each perimeter segment of the source parcel, detect which neighboring parcel(s) share that edge. Supports partial colindancias (multiple neighbors along one segment) and scenarios where a segment faces a public street.

## Requirements

### R-CD-01: R-tree candidate search

The system MUST build a QgsSpatialIndex from the adjacent pad layer. For each source segment, candidate parcels are gathered via bounding box intersection.

#### Scenario: Intersecting bounding box
- GIVEN a segment with a known bounding box
- WHEN the spatial index is queried
- THEN ALL parcels with overlapping bounding box are returned as candidates

### R-CD-02: Per-segment intersection

For each candidate, the system MUST compute the actual geometry intersection between the segment (as a QgsLineString) and the candidate's boundary. An intersection longer than zero (not a point) counts as a colindancia.

#### Scenario: exact edge match
- GIVEN a source segment whose line overlaps exactly with a neighbor's edge
- WHEN intersection is computed
- THEN the intersection length SHALL equal the segment length

#### Scenario: corner touching excluded
- GIVEN a source segment endpoint touching an adjacent parcel's corner
- WHEN intersection is computed
- THEN the intersection being a SHALL point NOT count as colindancia

### R-CD-03: Multiple neighbors per segment

A single segment MAY colindar partially with more than one neighbor. The system MUST detect and return all resulting subsegments with their respective neighbor.

#### Scenario: two neighbors along one segment
- GIVEN a 100m source segment where a neighbor occupies the first 60m and another occupies the remaining 40m
- WHEN colindancia detection runs
- THEN two subsegment colindancias are returned with distinct owners

### R-CD-04: Missing neighbors

A source segment with no intersection among candidates receives a null neighbor. The report SHOULD include a marker such as "Vía pública" or "Sin colindante".

#### Scenario: open face
- GIVEN a source segment not shared with any candidate parcel
- WHEN colindancia detection runs
- THEN the segment is returned with null neighbor

### EV-01: empty layer

If the adjacent layer is empty or not loaded, detection SHOULD gracefully return empty colindancias for all segments.
