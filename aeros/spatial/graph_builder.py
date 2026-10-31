"""Graph Construction Engine for AEROS Spatial Intelligence.

Constructs spatial graphs across Delhi NCR monitoring stations and grid cells:
- Strategy A: Distance-Based Adjacency Graph
- Strategy B: K-Nearest Neighbor (KNN) Topology
- Strategy C: Dynamic Meteorological Advection Graph
- Strategy D: Hybrid Geographical-Atmospheric Transport Graph

Generates PyTorch Geometric Data structures with node features, edge attributes,
and spatial holdout masks.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

from aeros.ingestion.cpcb import get_cpcb_stations
from aeros.ingestion.geospatial import calculate_bearing_degrees, haversine_distance_km
from aeros.spatial.distance_features import compute_geodesic_distance_matrix
from aeros.spatial.weather_edges import compute_meteorological_edges

logger = logging.getLogger("aeros.spatial.builder")


class AerosGraphBuilder:
    """Builder for static and dynamic spatial graph structures across Delhi NCR."""

    def __init__(
        self,
        stations: Optional[List[Dict[str, Any]]] = None,
        holdout_ids: List[str] = ["dwarka", "jahangirpuri", "mandir_marg"],
    ):
        self.stations = stations or get_cpcb_stations()
        self.holdout_ids = holdout_ids
        self.node_ids = [s["neighborhood_id"] for s in self.stations]
        self.id_to_idx = {nid: i for i, nid in enumerate(self.node_ids)}
        self.coords = [(s["latitude"], s["longitude"]) for s in self.stations]
        self.num_nodes = len(self.stations)
        self.dist_matrix = compute_geodesic_distance_matrix(self.coords)

    def build_distance_graph(
        self,
        distance_threshold_km: float = 25.0,
        decay_scale_km: float = 12.0,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Strategy A: Distance-based graph with Gaussian decay edge weights."""
        sources, targets, attrs = [], [], []

        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if i == j:
                    continue
                d = self.dist_matrix[i, j]
                if d <= distance_threshold_km:
                    w = float(np.exp(-((d / decay_scale_km) ** 2)))
                    sources.append(i)
                    targets.append(j)
                    attrs.append([d, w])

        edge_index = torch.tensor([sources, targets], dtype=torch.long)
        edge_attr = torch.tensor(attrs, dtype=torch.float32)
        return edge_index, edge_attr

    def build_knn_graph(self, k: int = 4) -> Tuple[torch.Tensor, torch.Tensor]:
        """Strategy B: K-Nearest Neighbor directed graph."""
        sources, targets, attrs = [], [], []

        for i in range(self.num_nodes):
            dists = self.dist_matrix[i].copy()
            dists[i] = float("inf")  # Exclude self
            nn_indices = np.argsort(dists)[:k]

            for j in nn_indices:
                d = float(dists[j])
                w = float(np.exp(-d / 12.0))
                sources.append(i)
                targets.append(j)
                attrs.append([d, w])

        edge_index = torch.tensor([sources, targets], dtype=torch.long)
        edge_attr = torch.tensor(attrs, dtype=torch.float32)
        return edge_index, edge_attr

    def build_hybrid_graph(
        self,
        wind_speed_ms: float = 2.5,
        wind_dir_deg: float = 315.0,
        max_dist_km: float = 28.0,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Strategy D: Hybrid geographical and meteorological wind-transport graph."""
        return compute_meteorological_edges(
            coords=self.coords,
            wind_speed_ms=wind_speed_ms,
            wind_dir_deg=wind_dir_deg,
            max_distance_km=max_dist_km,
        )

    def create_pyg_data_slice(
        self,
        df_timestamp_slice: pd.DataFrame,
        feature_cols: List[str],
        scaler,
        strategy: str = "hybrid",
        wind_speed_ms: float = 2.5,
        wind_dir_deg: float = 315.0,
    ) -> Data:
        """Assembles a PyG Data object for a single time slice across all stations."""
        # Align rows to node order
        node_features = []
        targets = []

        # Default fallback values if a station is momentarily missing in this time slice
        median_features = df_timestamp_slice[feature_cols].median().values

        for nid in self.node_ids:
            row = df_timestamp_slice[df_timestamp_slice["neighborhood_id"] == nid]
            if len(row) > 0:
                f_raw = row.iloc[0][feature_cols].values
                node_features.append(f_raw)
                targets.append([row.iloc[0]["pm2_5"], row.iloc[0]["pm10"]])
            else:
                node_features.append(median_features)
                targets.append([0.0, 0.0])

        x_arr = np.array(node_features, dtype=np.float32)
        x_scaled = scaler.transform(x_arr)
        x_tensor = torch.tensor(x_scaled, dtype=torch.float32)
        y_tensor = torch.tensor(np.array(targets), dtype=torch.float32)

        # Build edges based on selected strategy
        if strategy == "distance":
            edge_index, edge_attr = self.build_distance_graph()
        elif strategy == "knn":
            edge_index, edge_attr = self.build_knn_graph()
        elif strategy == "hybrid":
            edge_index, edge_attr = self.build_hybrid_graph(wind_speed_ms, wind_dir_deg)
        else:
            edge_index, edge_attr = self.build_distance_graph()

        # Spatial holdout masks
        train_mask = torch.tensor(
            [nid not in self.holdout_ids for nid in self.node_ids], dtype=torch.bool
        )
        test_mask = ~train_mask

        data = Data(
            x=x_tensor,
            edge_index=edge_index,
            edge_attr=edge_attr,
            y=y_tensor,
            train_mask=train_mask,
            test_mask=test_mask,
        )
        return data
