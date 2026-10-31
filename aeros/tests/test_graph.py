"""Unit tests for AEROS Spatial Grid and Graph Construction (Round 4)."""

import pytest
import torch

from aeros.spatial.distance_features import compute_geodesic_distance_matrix, compute_idw_weights
from aeros.spatial.graph_builder import AerosGraphBuilder
from aeros.spatial.grid_generator import DelhiGeospatialGrid
from aeros.spatial.weather_edges import compute_meteorological_edges


def test_grid_generation_structure():
    """Verify Delhi NCR grid geometry, cell bounds, and station associations."""
    grid = DelhiGeospatialGrid(resolution_deg=0.05)
    assert grid.total_cells == 121
    assert len(grid.grid_cells) == 121

    cell_0 = grid.grid_cells[0]
    assert "cell_id" in cell_0
    assert "centroid_lat" in cell_0
    assert "centroid_lon" in cell_0
    assert "bbox" in cell_0
    assert cell_0["bbox"]["lat_south"] < cell_0["bbox"]["lat_north"]
    assert cell_0["bbox"]["lon_west"] < cell_0["bbox"]["lon_east"]

    geojson = grid.to_geojson()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 121


def test_distance_and_knn_graph_strategies():
    """Verify distance-based and KNN graph builder methods."""
    builder = AerosGraphBuilder()
    edge_idx_dist, edge_attr_dist = builder.build_distance_graph(distance_threshold_km=25.0)
    assert edge_idx_dist.shape[0] == 2
    assert edge_attr_dist.shape[1] == 2
    assert edge_idx_dist.shape[1] > 0

    edge_idx_knn, edge_attr_knn = builder.build_knn_graph(k=3)
    assert edge_idx_knn.shape[0] == 2
    # Each node should have exactly k outgoing edges
    assert edge_idx_knn.shape[1] == builder.num_nodes * 3


def test_meteorological_advection_edges():
    """Verify directional wind projection in meteorological edge construction."""
    coords = [(28.60, 77.20), (28.65, 77.20)]  # Node 1 is south of Node 2
    # Wind from South (180 deg) blows North (towards 0 deg)
    edge_idx, edge_attr = compute_meteorological_edges(coords, wind_speed_ms=5.0, wind_dir_deg=180.0)
    assert edge_idx.shape[0] == 2
    assert edge_attr.shape[1] == 3  # [dist, alignment, transport_weight]

    # Node 0 -> Node 1 alignment should be strongly positive (downwind)
    assert edge_attr[0, 1] > 0.8
