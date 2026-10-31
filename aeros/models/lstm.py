"""LSTM Recurrent Neural Network for AEROS Time-Series Forecasting (Model B).

Implements a 2-layer multi-horizon LSTM network with dropout regularization,
layer normalization, and multi-step forecasting capabilities.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn

logger = logging.getLogger("aeros.models.lstm")


class AerosLSTM(nn.Module):
    """Multivariate LSTM forecasting model."""

    def __init__(
        self,
        in_features: int = 72,
        hidden_dim: int = 64,
        num_layers: int = 2,
        out_targets: int = 2,  # e.g., PM2.5 and PM10
        dropout: float = 0.2,
    ):
        super().__init__()
        self.in_features = in_features
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Input normalization / projection
        self.input_proj = nn.Linear(in_features, hidden_dim)

        # LSTM stack
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Output MLP head
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
        # Linear projection
        proj = self.input_proj(x)  # [B, T, hidden]

        # LSTM forward pass
        lstm_out, _ = self.lstm(proj)  # [B, T, hidden]

        # Take final temporal representation
        final_state = lstm_out[:, -1, :]  # [B, hidden]
        normed = self.norm(final_state)
        dropped = self.dropout(normed)

        hidden = self.act(self.fc1(dropped))
        out = self.fc2(hidden)
        return out


def save_lstm_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    val_loss: float,
    checkpoint_path: str = "aeros/artifacts/checkpoints/best_lstm.pt",
) -> None:
    """Saves best model checkpoint."""
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
    logger.info("Saved LSTM checkpoint to %s (Val Loss: %.4f)", checkpoint_path, val_loss)


def load_lstm_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/checkpoints/best_lstm.pt",
) -> float:
    """Loads checkpoint into model."""
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")
    chk = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(chk["model_state_dict"])
    logger.info("Loaded LSTM model from %s (Epoch %d, Val Loss: %.4f)", checkpoint_path, chk["epoch"], chk["val_loss"])
    return chk["val_loss"]
