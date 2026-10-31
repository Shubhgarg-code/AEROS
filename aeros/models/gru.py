"""GRU (Gated Recurrent Unit) Forecaster for AEROS (Model C).

Implements a 2-layer GRU architecture with layer normalization, dropout,
and multi-output forecasting for PM2.5 and PM10.
"""

import logging
import os
from typing import Dict, List, Optional
import torch
import torch.nn as nn

logger = logging.getLogger("aeros.models.gru")


class AerosGRU(nn.Module):
    """Multivariate GRU forecasting model."""

    def __init__(
        self,
        in_features: int = 72,
        hidden_dim: int = 64,
        num_layers: int = 2,
        out_targets: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.in_features = in_features
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.input_proj = nn.Linear(in_features, hidden_dim)

        self.gru = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden_dim // 2, out_targets)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        x: [batch_size, seq_len, in_features]
        returns: [batch_size, out_targets]
        """
        proj = self.input_proj(x)
        gru_out, _ = self.gru(proj)

        final_state = gru_out[:, -1, :]
        normed = self.norm(final_state)
        dropped = self.dropout(normed)

        hidden = self.act(self.fc1(dropped))
        out = self.fc2(hidden)
        return out


def save_gru_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    val_loss: float,
    checkpoint_path: str = "aeros/artifacts/checkpoints/best_gru.pt",
) -> None:
    """Saves best GRU model checkpoint."""
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "val_loss": val_loss,
        },
        checkpoint_path,
    )
    logger.info("Saved GRU checkpoint to %s (Val Loss: %.4f)", checkpoint_path, val_loss)


def load_gru_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/checkpoints/best_gru.pt",
) -> float:
    """Loads checkpoint into GRU model."""
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")
    chk = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(chk["model_state_dict"])
    logger.info("Loaded GRU model from %s (Epoch %d, Val Loss: %.4f)", checkpoint_path, chk["epoch"], chk["val_loss"])
    return chk["val_loss"]
