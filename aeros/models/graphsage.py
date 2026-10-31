"""GraphSAGE Architecture for Inductive Spatial Prediction (Model C).

Implements neighborhood aggregation via GraphSAGE (SAGEConv) to predict
pollutant concentrations at unseen geographical nodes during inductive inference.
"""

import logging
import os
from typing import Optional
import torch
import torch.nn as nn
from torch_geometric.nn import SAGEConv

logger = logging.getLogger("aeros.models.graphsage")


class AerosGraphSAGE(nn.Module):
    """Inductive GraphSAGE network for spatial pollution estimation."""

    def __init__(
        self,
        in_channels: int = 72,
        hidden_channels: int = 64,
        out_channels: int = 2,
        aggr: str = "mean",
        dropout: float = 0.2,
    ):
        super().__init__()
        self.sage1 = SAGEConv(in_channels, hidden_channels, aggr=aggr)
        self.sage2 = SAGEConv(hidden_channels, hidden_channels, aggr=aggr)
        self.norm = nn.LayerNorm(hidden_channels)
        self.act = nn.GELU()
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_channels, out_channels)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        x: [N, in_channels]
        edge_index: [2, E]
        returns: [N, out_channels]
        """
        h = self.sage1(x, edge_index)
        h = self.act(h)
        h = self.dropout(h)

        h = self.sage2(h, edge_index)
        h = self.norm(h)
        h = self.act(h)
        h = self.dropout(h)

        out = self.head(h)
        return out


def save_graphsage_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/spatial_models/best_graphsage.pt",
) -> None:
    """Saves GraphSAGE weights."""
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)
    logger.info("Saved GraphSAGE checkpoint to %s", checkpoint_path)


def load_graphsage_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/spatial_models/best_graphsage.pt",
) -> None:
    """Loads GraphSAGE weights."""
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
    logger.info("Loaded GraphSAGE checkpoint from %s", checkpoint_path)
