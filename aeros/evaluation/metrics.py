"""Evaluation Metrics and Diagnostic Engine for AEROS.

Computes standard atmospheric validation metrics (MAE, RMSE, R2, MAPE),
horizon-specific forecasting errors, Diwali event-segmented accuracy,
and conformal prediction interval calibration.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def compute_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    prefix: str = "",
) -> Dict[str, float]:
    """Computes MAE, RMSE, R2, and MAPE between true and predicted arrays."""
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    y_pred = np.asarray(y_pred, dtype=np.float64).ravel()

    # Drop any NaNs
    valid = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_t = y_true[valid]
    y_p = y_pred[valid]

    if len(y_t) == 0:
        return {
            f"{prefix}mae": 0.0,
            f"{prefix}rmse": 0.0,
            f"{prefix}r2": 0.0,
            f"{prefix}mape": 0.0,
            f"{prefix}samples": 0,
        }

    diff = y_t - y_p
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff**2)))

    # R2 calculation
    ss_tot = float(np.sum((y_t - np.mean(y_t)) ** 2))
    ss_res = float(np.sum(diff**2))
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-8 else 0.0

    # MAPE with epsilon threshold to prevent division by zero near zero concentrations
    epsilon = 1.0  # ug/m3
    mape = float(
        np.mean(np.abs(diff) / np.maximum(y_t, epsilon)) * 100.0
    )

    return {
        f"{prefix}mae": round(mae, 3),
        f"{prefix}rmse": round(rmse, 3),
        f"{prefix}r2": round(r2, 4),
        f"{prefix}mape": round(mape, 2),
        f"{prefix}samples": int(len(y_t)),
    }


def compute_horizon_metrics(
    y_true_dict: Dict[int, np.ndarray],
    y_pred_dict: Dict[int, np.ndarray],
    target_name: str = "pm2_5",
) -> Dict[str, Dict[str, float]]:
    """Computes metrics broken down by lead forecast horizon (1h, 3h, 6h, etc.)."""
    horizon_results = {}
    for h, y_t in y_true_dict.items():
        if h in y_pred_dict:
            y_p = y_pred_dict[h]
            metrics = compute_regression_metrics(
                y_t, y_p, prefix=f"{target_name}_"
            )
            horizon_results[f"{h}h"] = metrics
    return horizon_results


def evaluate_diwali_phases(
    df: pd.DataFrame,
    y_true_col: str,
    y_pred_col: str,
) -> Dict[str, Dict[str, float]]:
    """Evaluates error metrics across Pre-Diwali, Diwali Peak, and Post-Diwali regimes."""
    results = {}
    phase_col = "diwali_phase" if "diwali_phase" in df.columns else None

    if phase_col:
        for phase in ["pre_diwali", "diwali_peak", "post_diwali", "normal"]:
            subset = df[df[phase_col] == phase]
            if len(subset) > 0:
                results[phase] = compute_regression_metrics(
                    subset[y_true_col].values,
                    subset[y_pred_col].values,
                )
    else:
        results["overall"] = compute_regression_metrics(
            df[y_true_col].values,
            df[y_pred_col].values,
        )

    return results


def evaluate_conformal_calibration(
    y_true: np.ndarray,
    q_lower: np.ndarray,
    q_upper: np.ndarray,
    nominal_coverage: float = 0.90,
) -> Dict[str, float]:
    """Measures empirical coverage rate and mean interval width for uncertainty estimates."""
    y_t = np.asarray(y_true).ravel()
    q_l = np.asarray(q_lower).ravel()
    q_u = np.asarray(q_upper).ravel()

    covered = (y_t >= q_l) & (y_t <= q_u)
    empirical_coverage = float(np.mean(covered))
    interval_width = float(np.mean(q_u - q_l))

    return {
        "nominal_coverage": round(nominal_coverage, 3),
        "empirical_coverage": round(empirical_coverage, 3),
        "calibration_error": round(abs(empirical_coverage - nominal_coverage), 4),
        "mean_interval_width": round(interval_width, 2),
    }
