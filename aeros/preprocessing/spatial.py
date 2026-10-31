"""Spatial Preprocessing and Graph Intelligence for AEROS.

Computes pairwise Haversine distances, compass bearings, attaches OSM road density features,
and produces spatial adjacency representations for Graph Neural Networks.
"""

import json
import logging
import os
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

from aeros.ingestion.geospatial import calculate_bearing_degrees, haversine_distance_km
from aeros.ingestion.osm import get_osm_features

logger = logging.getLogger("aeros.preprocessing.spatial")


def build_spatial_feature_matrix(
    neighborhoods: List[Dict[str, Any]],
    output_dir: str = "aeros/data/features",
) -> pd.DataFrame:
    """Enriches neighborhood metadata with OpenStreetMap road density and morphology features."""
    os.makedirs(output_dir, exist_ok=True)
    records = []

    for nh in neighborhoods:
        osm_f = get_osm_features(nh["id"])
        record = {
            "neighborhood_id": nh["id"],
            "name": nh["name"],
            "latitude": nh["latitude"],
            "longitude": nh["longitude"],
            "zone": nh.get("zone", "Central"),
            "land_use": nh.get("land_use", "Mixed"),
            "road_density_factor": nh.get("road_density_factor", 1.0),
            "population_density_factor": nh.get("population_density_factor", 1.0),
            "road_density_km_per_km2": osm_f["road_density_km_per_km2"],
            "traffic_signal_density": osm_f["traffic_signal_density"],
            "industrial_fraction": osm_f["industrial_fraction"],
            "green_cover_fraction": osm_f["green_cover_fraction"],
            "bus_terminal_present": int(osm_f["bus_terminal_present"]),
            "railway_proximity_km": osm_f["railway_proximity_km"],
        }
        records.append(record)

    df_spatial = pd.DataFrame(records)
    out_path = os.path.join(output_dir, "neighborhood_spatial_features.parquet")
    df_spatial.to_parquet(out_path, index=False)
    csv_path = os.path.join(output_dir, "neighborhood_spatial_features.csv")
    df_spatial.to_csv(csv_path, index=False)
    logger.info("Saved spatial feature matrix (%d neighborhoods) to %s", len(df_spatial), out_path)
    return df_spatial


def compute_spatial_matrices(
    neighborhoods: List[Dict[str, Any]],
    distance_threshold_km: float = 30.0,
    decay_scale_km: float = 12.0,
) -> Dict[str, Any]:
    """Generates distance, bearing, and adjacency matrices."""
    n = len(neighborhoods)
    ids = [nh["id"] for nh in neighborhoods]

    dist_matrix = np.zeros((n, n), dtype=np.float32)
    bearing_matrix = np.zeros((n, n), dtype=np.float32)
    adjacency_matrix = np.zeros((n, n), dtype=np.float32)

    for i in range(n):
        for j in range(n):
            if i == j:
                dist_matrix[i, j] = 0.0
                bearing_matrix[i, j] = 0.0
                adjacency_matrix[i, j] = 1.0
            else:
                d = haversine_distance_km(
                    neighborhoods[i]["latitude"],
                    neighborhoods[i]["longitude"],
                    neighborhoods[j]["latitude"],
                    neighborhoods[j]["longitude"],
                )
                b = calculate_bearing_degrees(
                    neighborhoods[i]["latitude"],
                    neighborhoods[i]["longitude"],
                    neighborhoods[j]["latitude"],
                    neighborhoods[j]["longitude"],
                )
                dist_matrix[i, j] = d
                bearing_matrix[i, j] = b

                if d <= distance_threshold_km:
                    adjacency_matrix[i, j] = float(np.exp(-((d / decay_scale_km) ** 2)))

    return {
        "num_nodes": n,
        "neighborhood_ids": ids,
        "dist_matrix": dist_matrix.tolist(),
        "bearing_matrix": bearing_matrix.tolist(),
        "adjacency_matrix": adjacency_matrix.tolist(),
    }
