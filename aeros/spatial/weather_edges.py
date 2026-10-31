"""Dynamic Meteorological Edge Weighting Engine for AEROS.

Models advective atmospheric transport between geographical nodes based on
wind speed, wind direction azimuth, and pairwise bearing vectors.
"""

from typing import List, Tuple
import numpy as np
import torch

from aeros.ingestion.geospatial import calculate_bearing_degrees, haversine_distance_km


def compute_meteorological_edges(
    coords: List[Tuple[float, float]],
    wind_speed_ms: float,
    wind_dir_deg: float,
    max_distance_km: float = 30.0,
    advection_scale: float = 0.5,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Generates directed edges where edge attributes represent downwind transport intensity."""
    n = len(coords)
    sources, targets, attrs = [], [], []

    # Wind blowing FROM wind_dir_deg blows TOWARDS (wind_dir_deg + 180) % 360
    wind_towards_deg = (wind_dir_deg + 180.0) % 360.0
    wind_towards_rad = np.radians(wind_towards_deg)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue

            d = haversine_distance_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            if d > max_distance_km:
                continue

            bearing_deg = calculate_bearing_degrees(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            bearing_rad = np.radians(bearing_deg)

            # Cosine similarity between wind transport direction and vector from i to j
            alignment = float(np.cos(wind_towards_rad - bearing_rad))

            # Advection occurs when j is downwind of i (alignment > 0)
            downwind_flux = max(0.0, alignment) * (wind_speed_ms / 5.0) * advection_scale
            dist_decay = float(np.exp(-d / 12.0))

            # Edge attribute: [distance_km, alignment, transport_weight]
            transport_weight = (downwind_flux + 0.2) * dist_decay

            sources.append(i)
            targets.append(j)
            attrs.append([d, alignment, transport_weight])

    edge_index = torch.tensor([sources, targets], dtype=torch.long)
    edge_attr = torch.tensor(attrs, dtype=torch.float32)
    return edge_index, edge_attr
