"""Distance Feature Engineering and Spatial Weight Kernels for AEROS.

Computes geodesic pairwise distances, Gaussian exponential decay kernels,
and Inverse Distance Weighting (IDW) interpolation matrices.
"""

from typing import List, Tuple
import numpy as np

from aeros.ingestion.geospatial import haversine_distance_km


def compute_geodesic_distance_matrix(
    coords: List[Tuple[float, float]],
) -> np.ndarray:
    """Computes symmetric NxN distance matrix in kilometers."""
    n = len(coords)
    dist_matrix = np.zeros((n, n), dtype=np.float32)

    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_distance_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d

    return dist_matrix


def compute_gaussian_decay_weights(
    dist_matrix_km: np.ndarray,
    scale_km: float = 12.0,
    cutoff_km: float = 35.0,
) -> np.ndarray:
    """Computes Gaussian decay adjacency weights: A_ij = exp(-(d_ij / scale)^2) for d_ij <= cutoff."""
    weights = np.exp(-((dist_matrix_km / scale_km) ** 2)).astype(np.float32)
    weights[dist_matrix_km > cutoff_km] = 0.0
    np.fill_diagonal(weights, 1.0)
    return weights


def compute_idw_weights(
    target_coord: Tuple[float, float],
    source_coords: List[Tuple[float, float]],
    power: float = 2.0,
    epsilon_km: float = 0.1,
) -> np.ndarray:
    """Computes normalized Inverse Distance Weights (IDW) for an unmonitored point."""
    distances = np.array([
        haversine_distance_km(target_coord[0], target_coord[1], sc[0], sc[1])
        for sc in source_coords
    ], dtype=np.float32)

    # If target is virtually on top of a station, give 1.0 weight
    exact_idx = np.where(distances < epsilon_km)[0]
    if len(exact_idx) > 0:
        weights = np.zeros(len(source_coords), dtype=np.float32)
        weights[exact_idx[0]] = 1.0
        return weights

    inv_dist = 1.0 / (distances**power)
    weights = inv_dist / np.sum(inv_dist)
    return weights
