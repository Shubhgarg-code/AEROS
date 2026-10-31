"""Spatiotemporal Graph Neural Network (ST-GNN) for AEROS (Model D).

Combines temporal sequence encoding (recurrent GRU cell) with spatial graph attention
(GAT / GraphSAGE) and physics-informed advection-diffusion message passing.
"""

import logging
import os
from typing import Optional, Tuple
import torch
import torch.nn as nn
from torch_geometric.nn import GATConv

logger = logging.getLogger("aeros.models.st_gnn")


class AerosSpatiotemporalGNN(nn.Module):
    """Spatiotemporal Graph Neural Network: Temporal GRU -> Spatial GAT -> Prediction Head."""

    def __init__(
        self,
        in_features: int = 72,
        temporal_hidden: int = 48,
        spatial_hidden: int = 48,
        out_targets: int = 2,
        heads: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.in_features = in_features
        self.temporal_hidden = temporal_hidden
        self.spatial_hidden = spatial_hidden

        # Temporal Encoder: Processes historical sequence per node [N, T, F] -> [N, temporal_hidden]
        self.temporal_gru = nn.GRU(
            input_size=in_features,
            hidden_size=temporal_hidden,
            num_layers=1,
            batch_first=True,
        )

        # Spatial Graph Attention: Propagates information between neighbors [N, temporal_hidden]
        self.spatial_gat = GATConv(
            in_channels=temporal_hidden,
            out_channels=spatial_hidden,
            heads=heads,
            concat=False,
            dropout=dropout,
        )

        # Spatiotemporal Fusion & Regression Head
        self.norm = nn.LayerNorm(spatial_hidden + temporal_hidden)
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(spatial_hidden + temporal_hidden, 32)
        self.act = nn.GELU()
        self.head = nn.Linear(32, out_targets)

    def forward(
        self,
        x_seq: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass.

        x_seq: [num_nodes, seq_len, in_features]
        edge_index: [2, num_edges]
        returns: [num_nodes, out_targets]
        """
        # 1. Temporal encoding: Run GRU on sequence for each node
        gru_out, _ = self.temporal_gru(x_seq)  # [N, T, temporal_hidden]
        h_temporal = gru_out[:, -1, :]  # [N, temporal_hidden]

        # 2. Spatial Graph Attention message passing
        h_spatial = self.spatial_gat(h_temporal, edge_index)  # [N, spatial_hidden]
        h_spatial = self.act(h_spatial)

        # 3. Spatiotemporal Fusion
        h_fused = torch.cat([h_temporal, h_spatial], dim=-1)  # [N, temporal_hidden + spatial_hidden]
        h_fused = self.norm(h_fused)
        h_fused = self.dropout(h_fused)

        # 4. Prediction head
        out = self.head(self.act(self.fc1(h_fused)))
        return out


def save_stgnn_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/spatial_models/best_stgnn.pt",
) -> None:
    """Saves ST-GNN weights."""
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)
    logger.info("Saved ST-GNN checkpoint to %s", checkpoint_path)


def load_stgnn_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/spatial_models/best_stgnn.pt",
) -> None:
    """Loads ST-GNN weights."""
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
    logger.info("Loaded ST-GNN checkpoint from %s", checkpoint_path)
