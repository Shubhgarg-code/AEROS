"""Graph Attention Network (GAT) for AEROS Spatial Prediction (Model B).

Implements multi-head graph attention mechanisms to dynamically weight spatial
neighbors based on node atmospheric state and wind-transport alignment.
"""

import logging
import os
from typing import Optional, Tuple
import torch
import torch.nn as nn
from torch_geometric.nn import GATConv

logger = logging.getLogger("aeros.models.gat")


class AerosGAT(nn.Module):
    """Multi-Head Graph Attention Network for spatial pollution estimation."""

    def __init__(
        self,
        in_channels: int = 72,
        hidden_channels: int = 32,
        out_channels: int = 2,
        heads: int = 4,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.gat1 = GATConv(
            in_channels,
            hidden_channels,
            heads=heads,
            dropout=dropout,
            concat=True,
        )
        self.gat2 = GATConv(
            hidden_channels * heads,
            hidden_channels,
            heads=1,
            dropout=dropout,
            concat=False,
        )
        self.norm = nn.LayerNorm(hidden_channels)
        self.act = nn.ELU()
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_channels, out_channels)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        return_attention: bool = False,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """Forward pass with optional attention weight extraction."""
        if return_attention:
            h, (edge_index_attn, alpha) = self.gat1(x, edge_index, return_attention_weights=True)
            attn_weights = (edge_index_attn, alpha)
        else:
            h = self.gat1(x, edge_index)
            attn_weights = None

        h = self.act(h)
        h = self.dropout(h)

        h = self.gat2(h, edge_index)
        h = self.norm(h)
        h = self.act(h)
        h = self.dropout(h)

        out = self.head(h)
        return out, attn_weights


def save_gat_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/spatial_models/best_gat.pt",
) -> None:
    """Saves GAT weights."""
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)
    logger.info("Saved GAT checkpoint to %s", checkpoint_path)


def load_gat_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/spatial_models/best_gat.pt",
) -> None:
    """Loads GAT weights."""
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
    logger.info("Loaded GAT checkpoint from %s", checkpoint_path)
