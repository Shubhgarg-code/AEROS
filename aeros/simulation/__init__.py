"""AEROS Atmospheric Simulation and Scenario Intelligence Suite."""

from aeros.simulation.numerical_solver import Grid2DTransportSolver, GraphTransportSolver
from aeros.simulation.propagation import AtmosphericPropagationEngine
from aeros.simulation.scenarios import (
    SCENARIO_REGISTRY,
    ScenarioConfig,
    ScenarioType,
    compute_diurnal_traffic_profile,
    compute_firecracker_emission_pulse,
)
from aeros.simulation.counterfactual import DiwaliWhatIfSimulator
from aeros.simulation.recovery import AtmosphericRecoveryEngine, DEFAULT_THRESHOLDS

__all__ = [
    "Grid2DTransportSolver",
    "GraphTransportSolver",
    "AtmosphericPropagationEngine",
    "SCENARIO_REGISTRY",
    "ScenarioConfig",
    "ScenarioType",
    "compute_diurnal_traffic_profile",
    "compute_firecracker_emission_pulse",
    "DiwaliWhatIfSimulator",
    "AtmosphericRecoveryEngine",
    "DEFAULT_THRESHOLDS",
]
