"""Dynamic Spatial Graph Generation and Wind-Directed Advection Modeling for AEROS.

Builds static geographical adjacency and time-varying advection-diffusion
transport graph tensors where edge weights represent physical atmospheric
transport between neighborhood nodes.
"""

import json
import logging
import os
from typing import Any, Dict, List, Tuple
import numpy as np
import torch

logger = logging.getLogger("aeros.preprocessing.spatial_graph")
logging.basicConfig(level=logging.INFO)


class DynamicSpatialGraph:
    """Manages static spatial topology and time-resolved wind-directed propagation graphs."""

    def __init__(self, graph_json_path: str = "aeros/data/processed/spatial_graph.json"):
        if not os.path.exists(graph_json_path):
            raise FileNotFoundError(f"Spatial graph file not found at {graph_json_path}")

        with open(graph_json_path, "r", encoding="utf-8") as f:
            self.graph_data = json.load(f)

        self.num_nodes = self.graph_data["num_nodes"]
        self.neighborhood_ids = self.graph_data["neighborhood_ids"]
        self.id_to_idx = self.graph_data["id_to_idx"]
        self.dist_matrix = np.array(self.graph_data["distance_matrix_km"], dtype=np.float32)
        self.bearing_matrix = np.array(self.graph_data["bearing_matrix_deg"], dtype=np.float32)
        self.static_adj = np.array(self.graph_data["static_adjacency"], dtype=np.float32)

    def get_static_edge_index_and_attr(self, threshold_km: float = 25.0) -> Tuple[torch.Tensor, torch.Tensor]:
        """Returns standard PyTorch edge_index [2, E] and edge_attr [E, 2] (distance, static weight)."""
        sources, targets, attrs = [], [], []
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                d = self.dist_matrix[i, j]
                if d <= threshold_km and i != j:
                    sources.append(i)
                    targets.append(j)
                    w = self.static_adj[i, j]
                    attrs.append([d, w])

        edge_index = torch.tensor([sources, targets], dtype=torch.long)
        edge_attr = torch.tensor(attrs, dtype=torch.float32)
        return edge_index, edge_attr

    def compute_dynamic_transport_matrix(
        self,
        wind_speed_ms: float,
        wind_direction_deg: float,
        advection_scale: float = 0.35,
        diffusion_scale: float = 0.15,
        decay_km: float = 12.0,
    ) -> np.ndarray:
        """Computes physical atmospheric transport matrix between nodes.

        Wind blowing FROM theta blows TOWARDS (theta + 180) % 360.
        If bearing from i to j aligns with wind blow direction, pollution is advected from i to j.
        """
        # Direction where wind is blowing TOWARDS
        wind_towards_deg = (wind_direction_deg + 180.0) % 360.0
        wind_towards_rad = np.radians(wind_towards_deg)

        T = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float32)

        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if i == j:
                    T[i, j] = 1.0  # Retention / local source
                    continue

                d = self.dist_matrix[i, j]
                bearing_rad = np.radians(self.bearing_matrix[i, j])

                # Cosine similarity between wind velocity vector and ray from i to j
                # Positive when node j is downwind of node i
                wind_alignment = np.cos(wind_towards_rad - bearing_rad)

                # Distance damping
                dist_factor = np.exp(-d / decay_km)

                # Advective transport component (only positive forward transport)
                advection = max(0.0, float(wind_alignment)) * (wind_speed_ms / 5.0) * advection_scale

                # Isotropic turbulent diffusion component
                diffusion = diffusion_scale * dist_factor

                transport_weight = (advection + diffusion) * dist_factor
                T[i, j] = transport_weight

        # Normalize row-stochastically so sum(outflow) <= 1
        row_sums = T.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums > 0, row_sums, 1.0)
        T_normalized = T / row_sums
        return T_normalized
