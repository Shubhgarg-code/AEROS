"""Spatial Visualization and GeoJSON Heatmap Generation Engine for AEROS.

Generates full-coverage spatial predictions across the Delhi NCR grid, producing
GeoJSON heatmaps with PM2.5, PM10, uncertainty intervals, and graph edge connections
ready for web digital twin rendering.
"""

import json
import logging
import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from typing import Any, Dict, List, Optional
import numpy as np

from aeros.inference.neighborhood_predictor import AerosNeighborhoodPredictor
from aeros.spatial.grid_generator import DelhiGeospatialGrid

logger = logging.getLogger("aeros.evaluation.spatial_viz")


def generate_city_heatmap_geojson(
    output_path: str = "aeros/artifacts/graph_data/delhi_pollution_heatmap.geojson",
    weather_override: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Generates dense grid cell predictions across Delhi NCR."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    grid = DelhiGeospatialGrid(resolution_deg=0.05)
    predictor = AerosNeighborhoodPredictor()

    features = []
    pm25_values = []
    pm10_values = []

    for cell in grid.grid_cells:
        lat = cell["centroid_lat"]
        lon = cell["centroid_lon"]

        pred = predictor.predict_coordinate(
            latitude=lat,
            longitude=lon,
            weather_conditions=weather_override,
        )

        if pred.get("status") == "SUCCESS":
            p25 = pred["pm2_5"]["point_estimate"]
            p10 = pred["pm10"]["point_estimate"]
            pm25_values.append(p25)
            pm10_values.append(p10)

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
                    "centroid_lat": lat,
                    "centroid_lon": lon,
                    "pm2_5": p25,
                    "pm2_5_lower": pred["pm2_5"]["lower_bound"],
                    "pm2_5_upper": pred["pm2_5"]["upper_bound"],
                    "pm10": p10,
                    "pm10_lower": pred["pm10"]["lower_bound"],
                    "pm10_upper": pred["pm10"]["upper_bound"],
                    "confidence": pred["target_location"]["confidence_rating"],
                    "dist_to_monitor_km": pred["target_location"]["distance_to_nearest_monitor_km"],
                    "nearest_station": pred["nearest_monitoring_station"]["name"],
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": polygon_coords,
                },
            }
            features.append(feature)

    geojson_data = {
        "type": "FeatureCollection",
        "metadata": {
            "title": "AEROS Delhi NCR Spatial Pollution Heatmap",
            "total_cells": len(features),
            "pm25_range": [float(np.min(pm25_values)), float(np.max(pm25_values))],
            "pm10_range": [float(np.min(pm10_values)), float(np.max(pm10_values))],
        },
        "features": features,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)

    logger.info("Generated city heatmap GeoJSON with %d cells at %s", len(features), output_path)
    return geojson_data


if __name__ == "__main__":
    generate_city_heatmap_geojson()
