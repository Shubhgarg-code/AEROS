"""Unit tests for AEROS Training Checkpoints and State Persistence."""

import os
import pytest
import torch

from aeros.models.lstm import AerosLSTM, load_lstm_checkpoint, save_lstm_checkpoint


def test_lstm_checkpoint_save_and_load(tmp_path):
    """Verify LSTM state dict serialization and restoration."""
    chk_path = os.path.join(tmp_path, "test_lstm.pt")
    model = AerosLSTM(in_features=10, hidden_dim=16, num_layers=1, out_targets=2)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    save_lstm_checkpoint(model, optimizer, epoch=3, val_loss=12.5, checkpoint_path=chk_path)
    assert os.path.exists(chk_path)

    new_model = AerosLSTM(in_features=10, hidden_dim=16, num_layers=1, out_targets=2)
    loaded_val_loss = load_lstm_checkpoint(new_model, checkpoint_path=chk_path)
    assert loaded_val_loss == 12.5

    # Check weight equality
    for p1, p2 in zip(model.parameters(), new_model.parameters()):
        assert torch.equal(p1, p2)
