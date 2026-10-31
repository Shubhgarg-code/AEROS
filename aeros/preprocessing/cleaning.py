"""Dataset Cleaning and Quality Control for AEROS.

Handles outlier detection, statistical boundary capping, and missing-value imputation.
"""

import logging
from typing import List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("aeros.preprocessing.cleaning")
logging.basicConfig(level=logging.INFO)


def detect_and_cap_outliers(
    df: pd.DataFrame,
    columns: List[str],
    lower_quantile: float = 0.001,
    upper_quantile: float = 0.999,
) -> pd.DataFrame:
    """Cap extreme statistical anomalies using domain-aware atmospheric quantile boundaries."""
    cleaned = df.copy()
    for col in columns:
        if col in cleaned.columns:
            q_low = cleaned[col].quantile(lower_quantile)
            q_high = cleaned[col].quantile(upper_quantile)
            initial_anomalies = (
                (cleaned[col] < q_low) | (cleaned[col] > q_high)
            ).sum()
            if initial_anomalies > 0:
                logger.info(
                    "Capping %d statistical anomalies in column '%s' to [%.2f, %.2f]",
                    initial_anomalies,
                    col,
                    q_low,
                    q_high,
                )
                cleaned[col] = cleaned[col].clip(lower=q_low, upper=q_high)
    return cleaned


def impute_missing_data(df: pd.DataFrame) -> pd.DataFrame:
    """Imputes any remaining missing records using chronological forward/backward interpolation per station."""
    cleaned = df.copy()
    cleaned.sort_values(by=["neighborhood_id", "timestamp"], inplace=True)

    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        cleaned[col] = cleaned.groupby("neighborhood_id")[col].transform(
            lambda s: s.interpolate(method="linear").bfill().ffill()
        )

    # Fallback to global median if an entire station is empty for some column
    for col in numeric_cols:
        if cleaned[col].isna().any():
            median_val = cleaned[col].median()
            cleaned[col].fillna(median_val, inplace=True)

    return cleaned
