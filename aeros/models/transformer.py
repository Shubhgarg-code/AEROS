"""Temporal Transformer Forecaster for AEROS (Model D).

Implements a Time-Series Transformer with sinusoidal positional encodings,
multi-head self-attention, residual connections, and layer normalization.
"""

import math
import logging
import os
from typing import Dict, List, Optional
import torch
import torch.nn as nn

logger = logging.getLogger("aeros.models.transformer")


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for sequential temporal positions."""

    def __init__(self, d_model: int, max_len: int = 500, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [batch_size, seq_len, d_model]"""
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class AerosTransformer(nn.Module):
    """Time-series Transformer forecaster with multi-head self-attention."""

    def __init__(
        self,
        in_features: int = 72,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        out_targets: int = 2,
        dropout: float = 0.1,
        max_seq_len: int = 100,
    ):
        super().__init__()
        self.in_features = in_features
        self.d_model = d_model

        # Linear projection to d_model
        self.input_proj = nn.Linear(in_features, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len=max_seq_len, dropout=dropout)

        # Transformer Encoder Stack
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Final projection head
        self.norm = nn.LayerNorm(d_model)
        self.fc1 = nn.Linear(d_model, d_model // 2)
        self.act = nn.GELU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(d_model // 2, out_targets)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        x: [batch_size, seq_len, in_features]
        returns: [batch_size, out_targets]
        """
        proj = self.input_proj(x) * math.sqrt(self.d_model)
        encoded = self.pos_encoder(proj)
        out = self.transformer_encoder(encoded)  # [B, T, d_model]

        # Use pooled representation across sequence length
        pooled = self.norm(out[:, -1, :])  # [B, d_model]
        hidden = self.act(self.fc1(self.dropout(pooled)))
        final_preds = self.fc2(hidden)
        return final_preds


def save_transformer_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    val_loss: float,
    checkpoint_path: str = "aeros/artifacts/checkpoints/best_transformer.pt",
) -> None:
    """Saves best Transformer model checkpoint."""
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
    logger.info("Saved Transformer checkpoint to %s (Val Loss: %.4f)", checkpoint_path, val_loss)


def load_transformer_checkpoint(
    model: nn.Module,
    checkpoint_path: str = "aeros/artifacts/checkpoints/best_transformer.pt",
) -> float:
    """Loads checkpoint into Transformer model."""
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")
    chk = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(chk["model_state_dict"])
    logger.info("Loaded Transformer model from %s (Epoch %d, Val Loss: %.4f)", checkpoint_path, chk["epoch"], chk["val_loss"])
    return chk["val_loss"]
