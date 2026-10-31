"""Explainable AI (XAI) and Atmospheric Sensitivity Engine for AEROS.

Computes global feature importances, grouped domain sensitivities
(Meteorology, Historical Lags, Diwali Surge, Urban Built-Environment),
and local prediction attributions.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("aeros.evaluation.explainability")


def group_feature_importances(
    feature_importances: List[Dict[str, Any]],
) -> Dict[str, float]:
    """Groups individual feature gains into domain-informed physical atmospheric clusters."""
    groups = {
        "meteorological_transport": 0.0,
        "historical_autoregressive_lags": 0.0,
        "diwali_event_dynamics": 0.0,
        "temporal_solar_cycles": 0.0,
        "spatial_road_density": 0.0,
        "other": 0.0,
    }

    for item in feature_importances:
        feat = item["feature"]
        val = item["importance"]

        if any(w in feat for w in ["wind", "temperature", "humidity", "pressure", "stagnation", "dispersion", "precipitation"]):
            groups["meteorological_transport"] += val
        elif any(w in feat for w in ["lag", "rolling"]):
            groups["historical_autoregressive_lags"] += val
        elif any(w in feat for w in ["diwali", "hours_to_diwali"]):
            groups["diwali_event_dynamics"] += val
        elif any(w in feat for w in ["hour", "dow", "doy", "dayof"]):
            groups["temporal_solar_cycles"] += val
        elif any(w in feat for w in ["latitude", "longitude", "road", "population", "landuse"]):
            groups["spatial_road_density"] += val
        else:
            groups["other"] += val

    # Normalize to percentages
    total = sum(groups.values())
    if total > 0:
        return {k: round((v / total) * 100.0, 2) for k, v in groups.items()}
    return groups


def generate_explainability_report(
    xgb_forecaster: Any,
    horizons: List[int] = [1, 6, 24, 72],
    output_dir: str = "aeros/artifacts/reports",
) -> Dict[str, Any]:
    """Generates explainability report across lead forecast horizons."""
    os.makedirs(output_dir, exist_ok=True)
    report: Dict[str, Any] = {}

    for h in horizons:
        if h in xgb_forecaster.models:
            top_feats = xgb_forecaster.get_feature_importances(horizon=h, top_n=25)
            grouped = group_feature_importances(top_feats)
            report[f"{h}h"] = {
                "top_features": top_feats,
                "domain_importance_pct": grouped,
            }

    json_path = os.path.join(output_dir, "explainability_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Saved explainability audit to %s", json_path)
    return report
