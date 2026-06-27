"""Pipeline orchestrator — coordinates engine → template → output.

The :class:`PipelineOrchestrator` ties together geometry extraction,
bearing and distance computation, colindancia detection, and Jinja2
rendering into a single workflow.
"""

from typing import Any

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsPolygon,
    QgsVectorLayer,
)
from qgis.gui import QgisInterface

from derrotero_catastral.engine.bearing import (
    compute_azimuth,
    to_cardinal,
    to_quadrant_bearing,
)
from derrotero_catastral.engine.colindancia import build_index, find_colindancias
from derrotero_catastral.engine.distance import compute_distance
from derrotero_catastral.engine.geometry import extract_vertices, linearize_curve, order_nw
from derrotero_catastral.engine.types import SegmentData, Vertex
from derrotero_catastral.template.environment import create_environment
from derrotero_catastral.template.variables import build_context


class PipelineOrchestrator:
    """Coordinates the full derrotero generation pipeline.

    Flow: feature geometry → vertex extraction → NW ordering →
    bearing + distance computation → colindancia detection →
    context building → Jinja2 rendering.
    """

    def __init__(self, iface: QgisInterface) -> None:
        self.iface = iface

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        layer: QgsVectorLayer,
        feature_id: int,
        colindancia_layer: QgsVectorLayer | None = None,
        template_name: str = "es.j2",
        locale: str = "es",
    ) -> str:
        """Execute the full derrotero generation pipeline.

        Parameters
        ----------
        layer
            Source polygon layer containing the feature to process.
        feature_id
            Feature ID of the parcel to generate the derrotero for.
        colindancia_layer
            Optional polygon layer with neighbouring parcels for
            colindancia detection.  When ``None``, no colindancia
            information is included.
        template_name
            Jinja2 template filename (default ``"es.j2"``).
        locale
            Locale used for cardinal direction labels (default ``"es"``).

        Returns
        -------
        str
            Rendered derrotero text.

        Raises
        ------
        ValueError
            If the feature has no geometry, the CRS is invalid, the
            geometry is not a polygon, or the template is not found.
        RuntimeError
            If the Jinja2 template rendering fails.
        """
        # ------------------------------------------------------------------
        # 1. Obtain feature and geometry
        # ------------------------------------------------------------------
        feature: QgsFeature = layer.getFeature(feature_id)
        if not feature.hasGeometry():
            raise ValueError(
                f"Feature FID {feature_id} has no geometry — "
                "cannot generate derrotero."
            )

        geom = feature.geometry()
        if geom.isEmpty():
            raise ValueError(
                f"Feature FID {feature_id} has an empty geometry."
            )

        crs: QgsCoordinateReferenceSystem = layer.crs()
        if not crs.isValid():
            raise ValueError(
                f"Layer '{layer.name()}' has an invalid CRS."
            )

        # ------------------------------------------------------------------
        # 2. Linearise curves and ensure the geometry is a polygon
        # ------------------------------------------------------------------
        abstract = linearize_curve(geom.constGet())
        if not isinstance(abstract, QgsPolygon):
            raise ValueError(
                "Geometry is not a polygon — derrotero generation "
                "requires a polygon layer."
            )

        # ------------------------------------------------------------------
        # 3. Extract vertices and order NW
        # ------------------------------------------------------------------
        vertices: list[Vertex] = extract_vertices(abstract)
        if len(vertices) < 2:
            raise ValueError(
                "Polygon has fewer than 2 vertices after extraction."
            )

        ordered: list[Vertex] = order_nw(vertices)

        # ------------------------------------------------------------------
        # 4. Build colindancia spatial index (if applicable)
        # ------------------------------------------------------------------
        col_index = None
        if colindancia_layer is not None:
            col_index = build_index(colindancia_layer)

        # ------------------------------------------------------------------
        # 5. Compute segments — bearing, distance, colindancia
        # ------------------------------------------------------------------
        segments: list[SegmentData] = []
        n = len(ordered)
        for i in range(n):
            a: Vertex = ordered[i]
            b: Vertex = ordered[(i + 1) % n]

            azimut: float = compute_azimuth(a, b)
            rumbo: str = to_quadrant_bearing(azimut)
            orientacion: str = to_cardinal(azimut, locale)
            distancia: float = compute_distance(a, b, crs)

            segment_tuple: tuple[float, float, float, float] = (
                a.x,
                a.y,
                b.x,
                b.y,
            )

            colindancia: str | None = None
            if col_index is not None and colindancia_layer is not None:
                cols = find_colindancias(
                    i, segment_tuple, col_index, colindancia_layer
                )
                if cols:
                    # Use the best-match (first returned) colindancia
                    colindancia = cols[0].neighbor_owner

            segments.append(
                SegmentData(
                    v_origen=a.index,
                    v_destino=b.index,
                    x1=a.x,
                    y1=a.y,
                    x2=b.x,
                    y2=b.y,
                    distancia=distancia,
                    azimut=azimut,
                    rumbo=rumbo,
                    orientacion=orientacion,
                    colindancia=colindancia,
                )
            )

        # ------------------------------------------------------------------
        # 6. Build polygon attributes from feature fields
        # ------------------------------------------------------------------
        polygon_attributes: dict[str, Any] = {}
        fields = layer.fields()
        for i in range(fields.count()):
            polygon_attributes[fields.field(i).name()] = feature.attribute(i)

        # ------------------------------------------------------------------
        # 7. Build Jinja2 context
        # ------------------------------------------------------------------
        context: dict[str, Any] = build_context(
            segments, polygon_attributes, locale
        )

        # ------------------------------------------------------------------
        # 8. Create environment and render template
        # ------------------------------------------------------------------
        import os

        plugin_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        builtin_dir = os.path.join(plugin_dir, "template", "blueprints")

        env = create_environment(builtin_dir=builtin_dir)

        try:
            template = env.get_template(template_name)
        except Exception as exc:
            raise ValueError(
                f"Template '{template_name}' not found: {exc}"
            ) from exc

        try:
            output: str = template.render(**context)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to render template '{template_name}': {exc}"
            ) from exc

        return output
