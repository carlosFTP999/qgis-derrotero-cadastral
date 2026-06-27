"""Core data types for the derrotero engine."""

from typing import NamedTuple


class Vertex(NamedTuple):
    """A single vertex in a polygon perimeter.

    Attributes:
        index: Zero-based position in the vertex sequence.
        x: X coordinate (easting) in the source CRS.
        y: Y coordinate (northing) in the source CRS.
    """

    index: int
    x: float
    y: float


class SegmentData(NamedTuple):
    """Computed data for a single perimeter segment.

    Attributes:
        v_origen: Vertex index of the segment start.
        v_destino: Vertex index of the segment end.
        x1, y1: Coordinates of the start point.
        x2, y2: Coordinates of the end point.
        distancia: Geodetic length in meters.
        azimut: Forward azimuth from start to end (0-360°).
        rumbo: Quadrant bearing string (e.g. "N 45° E").
        orientacion: Cardinal orientation (e.g. "Noreste").
        colindancia: Name of the adjoining parcel owner, or None.
    """

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
    colindancia: str | None

    @property
    def length_m(self) -> str:
        """Return the segment distance formatted with 3 decimal places."""
        return f"{self.distancia:.3f}"


class Colindancia(NamedTuple):
    """An adjoining parcel (colindancia) detected for a segment.

    Attributes:
        segment_idx: Index of the polygon segment.
        neighbor_fid: Feature ID of the adjoining parcel.
        neighbor_owner: Owner name of the adjoining parcel, or None.
        overlap_length: Shared boundary length in meters.
    """

    segment_idx: int
    neighbor_fid: int
    neighbor_owner: str | None
    overlap_length: float
