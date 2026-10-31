"""Spatial Validation, Error Stratification, and Distance Sensitivity Engine for AEROS.

Evaluates spatial generalization error stratified by:
1. Geographical zone (North, South, East, West, Central)
2. Distance from nearest physical monitoring station (<5km, 5-10km, >10km)
3. Station density regime (Dense urban core vs. peri-urban border zones)
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from aeros.evaluation.metrics import compute_regression_metrics

logger = logging.getLogger("aeros.spatial.validation")


def stratify_errors_by_distance(
    df_eval: pd.DataFrame,
    dist_col: str = "dist_to_nearest_station_km",
    true_col: str = "true_pm25",
    pred_col: str = "pred_pm25",
) -> Dict[str, Dict[str, float]]:
    """Analyzes predictive error degradation as distance from nearest monitoring station increases."""
    bins = [0.0, 5.0, 10.0, 50.0]
    labels = ["near_0_to_5km", "mid_5_to_10km", "far_gt_10km"]

    df = df_eval.copy()
    df["dist_bucket"] = pd.cut(df[dist_col], bins=bins, labels=labels, right=True)

    results = {}
    for label in labels:
        subset = df[df["dist_bucket"] == label]
        if len(subset) > 0:
            results[label] = compute_regression_metrics(
                subset[true_col].values,
                subset[pred_col].values,
                prefix="pm25_",
            )
        else:
            results[label] = {"pm25_mae": 0.0, "pm25_rmse": 0.0, "pm25_samples": 0}

    return results


def stratify_errors_by_zone(
    df_eval: pd.DataFrame,
    zone_col: str = "zone",
    true_col: str = "true_pm25",
    pred_col: str = "pred_pm25",
) -> Dict[str, Dict[str, float]]:
    """Computes error metrics broken down by administrative / geographical zone."""
    results = {}
    if zone_col in df_eval.columns:
        for z in df_eval[zone_col].unique():
            sub = df_eval[df_eval[zone_col] == z]
            if len(sub) > 0:
                results[str(z)] = compute_regression_metrics(
                    sub[true_col].values,
                    sub[pred_col].values,
                    prefix="pm25_",
                )
    return results
