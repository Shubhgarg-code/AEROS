"""Unit tests for AEROS Spatial Intelligence and Geodesic Functions."""

import numpy as np
import pytest

from aeros.ingestion.geospatial import calculate_bearing_degrees, haversine_distance_km
from aeros.ingestion.osm import get_osm_features
from aeros.preprocessing.spatial import compute_spatial_matrices


def test_haversine_distance():
    """Verify known distances between landmarks in Delhi.

    Anand Vihar (28.6469, 77.3160) to Connaught Place (28.6315, 77.2167) is approx 9.8 km.
    """
    d = haversine_distance_km(28.6469, 77.3160, 28.6315, 77.2167)
    assert 9.0 <= d <= 11.0


def test_bearing_calculation():
    """Verify bearing angles. Moving strictly North should be bearing 0 degrees."""
    # From (28.0, 77.0) to (29.0, 77.0)
    b_north = calculate_bearing_degrees(28.0, 77.0, 29.0, 77.0)
    assert abs(b_north - 0.0) < 1.0 or abs(b_north - 360.0) < 1.0

    # Moving strictly East should be bearing 90 degrees
    b_east = calculate_bearing_degrees(28.0, 77.0, 28.0, 78.0)
    assert 85.0 <= b_east <= 95.0


def test_osm_features_retrieval():
    """Verify OSM road density attributes for known hotspots."""
    av_features = get_osm_features("anand_vihar")
    assert av_features["road_density_km_per_km2"] > 10.0
    assert av_features["bus_terminal_present"] is True


def test_spatial_matrices_construction():
    """Verify symmetry and properties of distance and adjacency matrices."""
    sample_nodes = [
        {"id": "n1", "name": "Node 1", "latitude": 28.60, "longitude": 77.20},
        {"id": "n2", "name": "Node 2", "latitude": 28.65, "longitude": 77.25},
    ]
    matrices = compute_spatial_matrices(sample_nodes)
    dist = np.array(matrices["dist_matrix"])
    adj = np.array(matrices["adjacency_matrix"])

    assert dist.shape == (2, 2)
    assert dist[0, 0] == 0.0
    assert abs(dist[0, 1] - dist[1, 0]) < 1e-4  # Symmetric distance
    assert adj[0, 0] == 1.0  # Self-loop
    assert 0.0 <= adj[0, 1] <= 1.0  # Decayed weight
