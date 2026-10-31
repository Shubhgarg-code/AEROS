"""Unit tests for Spatial Graph Neural Network Architectures (Round 4)."""

import pytest
import torch

from aeros.models.gat import AerosGAT
from aeros.models.gcn import AerosGCN
from aeros.models.graphsage import AerosGraphSAGE
from aeros.models.spatiotemporal_gnn import AerosSpatiotemporalGNN


def test_gcn_spatial_forward():
    """Verify GCN message passing and output shape [N, 2]."""
    model = AerosGCN(in_channels=16, hidden_channels=32, out_channels=2)
    x = torch.randn(10, 16)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)
    out = model(x, edge_index)
    assert out.shape == (10, 2)
    assert not torch.isnan(out).any()


def test_gat_spatial_forward():
    """Verify GAT multi-head attention and attention weight extraction."""
    model = AerosGAT(in_channels=16, hidden_channels=16, out_channels=2, heads=2)
    x = torch.randn(8, 16)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)
    out, attn = model(x, edge_index, return_attention=True)
    assert out.shape == (8, 2)
    assert attn is not None
    assert attn[0].shape[0] == 2  # edge_index_attn


def test_graphsage_spatial_forward():
    """Verify GraphSAGE inductive neighborhood aggregation."""
    model = AerosGraphSAGE(in_channels=16, hidden_channels=32, out_channels=2, aggr="mean")
    x = torch.randn(12, 16)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)
    out = model(x, edge_index)
    assert out.shape == (12, 2)


def test_spatiotemporal_gnn_forward():
    """Verify Spatiotemporal GNN forward pass on temporal sequence graph [N, T, F]."""
    model = AerosSpatiotemporalGNN(in_features=16, temporal_hidden=24, spatial_hidden=24, out_targets=2, heads=2)
    # [num_nodes=6, seq_len=4, in_features=16]
    x_seq = torch.randn(6, 4, 16)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)
    out = model(x_seq, edge_index)
    assert out.shape == (6, 2)
    assert not torch.isnan(out).any()
