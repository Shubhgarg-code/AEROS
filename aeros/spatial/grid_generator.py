"""Geographical Grid Generation System for AEROS.

Divides the Delhi NCR region into a uniform spatial grid with configurable resolution,
assigns unique cell identifiers, computes cell centroids, maps physical CAAQMS stations
to their containing cells, and produces GeoJSON structures for spatial rendering.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from aeros.ingestion.cpcb import get_cpcb_stations
from aeros.ingestion.geospatial import haversine_distance_km

logger = logging.getLogger("aeros.spatial.grid")

# Delhi NCR Regional Boundaries
DELHI_BOUNDS = {
    "lat_min": 28.38,
    "lat_max": 28.88,
    "lon_min": 76.90,
    "lon_max": 77.40,
}


class DelhiGeospatialGrid:
    """Manages uniform discrete geographical cells across Delhi NCR."""

    def __init__(
        self,
        bounds: Optional[Dict[str, float]] = None,
        resolution_deg: float = 0.05,  # approx 5.5 km resolution
    ):
        self.bounds = bounds or DELHI_BOUNDS
        self.resolution = resolution_deg

        # Generate coordinate arrays
        self.lats = np.arange(self.bounds["lat_min"], self.bounds["lat_max"] + 1e-5, self.resolution)
        self.lons = np.arange(self.bounds["lon_min"], self.bounds["lon_max"] + 1e-5, self.resolution)
        self.num_rows = len(self.lats)
        self.num_cols = len(self.lons)
        self.total_cells = self.num_rows * self.num_cols

        self.stations = get_cpcb_stations()
        self.grid_cells: List[Dict[str, Any]] = []
        self._build_grid()

    def _build_grid(self) -> None:
        """Constructs all grid cell centroids, boundaries, and station associations."""
        half_res = self.resolution / 2.0

        for r, lat in enumerate(self.lats):
            for c, lon in enumerate(self.lons):
                cell_id = f"grid_r{r:02d}_c{c:02d}"

                # Calculate boundary coordinates (BBOX)
                box = {
                    "lat_south": round(float(lat - half_res), 5),
                    "lat_north": round(float(lat + half_res), 5),
                    "lon_west": round(float(lon - half_res), 5),
                    "lon_east": round(float(lon + half_res), 5),
                }

                # Find stations residing inside this cell
                contained_stations = []
                for st in self.stations:
                    if (box["lat_south"] <= st["latitude"] < box["lat_north"]) and (
                        box["lon_west"] <= st["longitude"] < box["lon_east"]
                    ):
                        contained_stations.append(st["neighborhood_id"])

                # Calculate distance to closest monitoring station
                min_dist_to_station = float("inf")
                closest_station = None
                for st in self.stations:
                    d = haversine_distance_km(lat, lon, st["latitude"], st["longitude"])
                    if d < min_dist_to_station:
                        min_dist_to_station = d
                        closest_station = st["neighborhood_id"]

                self.grid_cells.append({
                    "cell_id": cell_id,
                    "row": r,
                    "col": c,
                    "centroid_lat": round(float(lat), 5),
                    "centroid_lon": round(float(lon), 5),
                    "bbox": box,
                    "is_monitored": len(contained_stations) > 0,
                    "monitoring_stations": contained_stations,
                    "nearest_station_id": closest_station,
                    "dist_to_nearest_station_km": round(min_dist_to_station, 2),
                })

        logger.info(
            "Constructed Delhi NCR grid: %d rows x %d cols = %d cells (Monitored cells: %d)",
            self.num_rows,
            self.num_cols,
            self.total_cells,
            sum(1 for c in self.grid_cells if c["is_monitored"]),
        )

    def to_geojson(self) -> Dict[str, Any]:
        """Converts grid cells into standard GeoJSON FeatureCollection."""
        features = []
        for cell in self.grid_cells:
            b = cell["bbox"]
            polygon_coords = [[
                [b["lon_west"], b["lat_south"]],
                [b["lon_east"], b["lat_south"]],
                [b["lon_east"], b["lat_north"]],
                [b["lon_west"], b["lat_north"]],
                [b["lon_west"], b["lat_south"]],
            ]]

            feature = {
                "type": "Feature",
                "id": cell["cell_id"],
                "properties": {
                    "cell_id": cell["cell_id"],
                    "centroid_lat": cell["centroid_lat"],
                    "centroid_lon": cell["centroid_lon"],
                    "is_monitored": cell["is_monitored"],
                    "monitoring_stations": cell["monitoring_stations"],
                    "nearest_station_id": cell["nearest_station_id"],
                    "dist_to_nearest_station_km": cell["dist_to_nearest_station_km"],
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": polygon_coords,
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "metadata": {
                "bounds": self.bounds,
                "resolution_deg": self.resolution,
                "total_cells": self.total_cells,
            },
            "features": features,
        }

    def save(self, output_dir: str = "aeros/artifacts/graph_data") -> str:
        """Exports grid metadata and GeoJSON."""
        os.makedirs(output_dir, exist_ok=True)
        geojson_path = os.path.join(output_dir, "delhi_ncr_grid.geojson")
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(self.to_geojson(), f, indent=2)

        json_path = os.path.join(output_dir, "delhi_ncr_grid.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.grid_cells, f, indent=2)

        logger.info("Saved grid GeoJSON to %s", geojson_path)
        return geojson_path
