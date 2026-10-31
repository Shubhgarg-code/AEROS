"""Geospatial Intelligence and Spatial Graph Topology Module for AEROS.

Computes pairwise Haversine geodesic distances, bearing angles, and spatial
neighborhood connectivity matrices across Delhi NCR coordinates.
"""

import json
import logging
import os
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("aeros.ingestion.geospatial")
logging.basicConfig(level=logging.INFO)


def haversine_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculate the great circle distance between two points on the earth in km."""
    R = 6371.0  # Earth radius in kilometers
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = (
        np.sin(dphi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return float(R * c)


def calculate_bearing_degrees(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculate the compass bearing (azimuth in degrees [0, 360)) from point 1 to point 2."""
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dlambda = np.radians(lon2 - lon1)

    y = np.sin(dlambda) * np.cos(phi2)
    x = np.cos(phi1) * np.sin(phi2) - np.sin(phi1) * np.cos(phi2) * np.cos(
        dlambda
    )
    bearing = np.degrees(np.arctan2(y, x))
    return float((bearing + 360) % 360)


def build_neighborhood_spatial_graph(
    neighborhoods: List[Dict[str, Any]],
    distance_threshold_km: float = 25.0,
    decay_scale_km: float = 10.0,
    output_dir: str = "aeros/data/processed",
) -> Dict[str, Any]:
    """Constructs pairwise distance, bearing, and spatial adjacency graphs."""
    os.makedirs(output_dir, exist_ok=True)
    n = len(neighborhoods)
    ids = [nh["id"] for nh in neighborhoods]
    id_to_idx = {nh_id: i for i, nh_id in enumerate(ids)}

    dist_matrix = np.zeros((n, n), dtype=np.float32)
    bearing_matrix = np.zeros((n, n), dtype=np.float32)
    static_adj_matrix = np.zeros((n, n), dtype=np.float32)

    edges: List[Dict[str, Any]] = []

    for i in range(n):
        nh1 = neighborhoods[i]
        for j in range(n):
            if i == j:
                dist_matrix[i, j] = 0.0
                bearing_matrix[i, j] = 0.0
                static_adj_matrix[i, j] = 1.0  # Self-loop
            else:
                nh2 = neighborhoods[j]
                d = haversine_distance_km(
                    nh1["latitude"],
                    nh1["longitude"],
                    nh2["latitude"],
                    nh2["longitude"],
                )
                b = calculate_bearing_degrees(
                    nh1["latitude"],
                    nh1["longitude"],
                    nh2["latitude"],
                    nh2["longitude"],
                )
                dist_matrix[i, j] = d
                bearing_matrix[i, j] = b

                if d <= distance_threshold_km:
                    # Gaussian distance decay weight
                    w = float(np.exp(-((d / decay_scale_km) ** 2)))
                    static_adj_matrix[i, j] = w
                    edges.append({
                        "source": nh1["id"],
                        "target": nh2["id"],
                        "source_idx": i,
                        "target_idx": j,
                        "distance_km": round(d, 3),
                        "bearing_deg": round(b, 2),
                        "weight": round(w, 4),
                    })

    graph_data = {
        "num_nodes": n,
        "neighborhood_ids": ids,
        "id_to_idx": id_to_idx,
        "distance_matrix_km": dist_matrix.tolist(),
        "bearing_matrix_deg": bearing_matrix.tolist(),
        "static_adjacency": static_adj_matrix.tolist(),
        "edge_list": edges,
        "node_metadata": neighborhoods,
    }

    graph_path = os.path.join(output_dir, "spatial_graph.json")
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)

    logger.info(
        "Built spatial graph with %d nodes and %d directed edges. Saved to %s",
        n,
        len(edges),
        graph_path,
    )
    return graph_data
