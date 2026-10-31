"""Graph Convolutional Network (GCN) for AEROS Spatial Prediction (Model A).

Implements a 2-layer Graph Convolutional Network for predicting continuous
particulate matter concentrations across spatial graph nodes.
"""

import logging
import os
from typing import Optional, Tuple
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv

logger = logging.getLogger("aeros.models.gcn")


class AerosGCN(nn.Module):
    """2-Layer Graph Convolutional Network for spatial pollution estimation."""

    def __init__(
        self,
        in_channels: int = 72,
        hidden_channels: int = 64,
        out_channels: int = 2,  # PM2.5 and PM10
        dropout: float = 0.2,
    ):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.norm = nn.LayerNorm(hidden_channels)
        self.act = nn.GELU()
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_channels, out_channels)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Forward pass.

        x: [N, in_channels]
        edge_index: [2, E]
        edge_weight: [E] optional
        returns: [N, out_channels]
        """
        h = self.conv1(x, edge_index, edge_weight)
        h = self.act(h)
        h = self.dropout(h)

        h = self.conv2(h, edge_index, edge_weight)
        h = self.norm(h)
        h = self.act(h)
        h = self.dropout(h)

        out = self.head(h)
        return out


def save_gcn_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/spatial_models/best_gcn.pt",
) -> None:
    """Saves GCN weights."""
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)
    logger.info("Saved GCN checkpoint to %s", checkpoint_path)


def load_gcn_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/spatial_models/best_gcn.pt",
) -> None:
    """Loads GCN weights."""
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
    logger.info("Loaded GCN checkpoint from %s", checkpoint_path)
