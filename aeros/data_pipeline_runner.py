"""AEROS End-to-End Data Engineering Pipeline Runner.

Orchestrates:
1. Multi-source Ingestion: CPCB / Open-Meteo Air Quality, Open-Meteo Weather, ERA5 Atmospheric Layers, OpenStreetMap Road Density.
2. Spatial Graph Topology & Haversine Distance/Bearing Matrices.
3. Physical Validation & Consistency Enforcement (PM10 >= PM2.5, Coordinate Bounding).
4. Statistical Outlier Capping and Quality Control.
5. High-dimensional Feature Engineering (Cycles, Diwali Pulse, Wind u/v, Lags, Rolling Windows).
6. Multi-Horizon Forward Targets (1h, 3h, 6h, 12h, 24h, 48h, 72h).
7. Leakage-free Chronological and Spatial Holdout Splitting.
8. Fitting and Serialization of RobustScalers strictly on Training Split.
9. Automated Generation of Data Quality Reports (JSON & Markdown).
"""

import json
import logging
import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

import yaml

from aeros.ingestion.air_quality import fetch_all_air_quality
from aeros.ingestion.cpcb import export_cpcb_station_metadata
from aeros.ingestion.era5 import fetch_era5_atmospheric_profile
from aeros.ingestion.osm import export_osm_features
from aeros.ingestion.validation import merge_air_quality_and_weather
from aeros.ingestion.weather import fetch_all_weather
from aeros.preprocessing.cleaning import detect_and_cap_outliers, impute_missing_data
from aeros.preprocessing.dataset_builder import build_and_save_datasets
from aeros.preprocessing.datasets import create_multi_horizon_targets
from aeros.preprocessing.features import engineer_all_features
from aeros.preprocessing.spatial import build_spatial_feature_matrix, compute_spatial_matrices
from aeros.preprocessing.validation import (
    remove_duplicates_and_sort,
    validate_coordinates,
    validate_physical_consistency,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aeros.pipeline_runner")


def run_pipeline(force_download: bool = False) -> None:
    """Executes the complete Round 2 data engineering pipeline."""
    logger.info("==================================================")
    logger.info("   STARTING AEROS DATA ENGINEERING PIPELINE       ")
    logger.info("==================================================")

    # 1. Load Configurations
    with open("aeros/configs/data_config.yaml", "r", encoding="utf-8") as f:
        data_cfg = yaml.safe_load(f)
    with open("aeros/configs/training_config.yaml", "r", encoding="utf-8") as f:
        train_cfg = yaml.safe_load(f)

    neighborhoods = data_cfg["neighborhoods"]
    diwali_windows = data_cfg["diwali_windows"]
    horizons = train_cfg["evaluation"]["horizons"]

    raw_dir = train_cfg["paths"]["raw_data_dir"]
    proc_dir = train_cfg["paths"]["processed_data_dir"]
    feat_dir = "aeros/data/features"
    scalers_dir = train_cfg["paths"]["scalers_dir"]
    reports_dir = "aeros/reports"

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(feat_dir, exist_ok=True)
    os.makedirs(scalers_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # 2. Metadata & External Geospatial Ingestion
    logger.info("Step 1: Ingesting CPCB Metadata & OpenStreetMap Built-Environment Features...")
    export_cpcb_station_metadata(output_dir=proc_dir)
    export_osm_features(output_path="aeros/data/external/osm_road_density.json")
    build_spatial_feature_matrix(neighborhoods, output_dir=feat_dir)
    spatial_matrices = compute_spatial_matrices(neighborhoods)
    with open(os.path.join(proc_dir, "spatial_matrices.json"), "w", encoding="utf-8") as f:
        json.dump(spatial_matrices, f, indent=2)

    # 3. Air Quality & Weather Ingestion
    aq_raw_path = os.path.join(raw_dir, "air_quality_raw.parquet")
    w_raw_path = os.path.join(raw_dir, "weather_raw.parquet")

    if not force_download and os.path.exists(aq_raw_path) and os.path.exists(w_raw_path):
        import pandas as pd
        logger.info("Step 2: Found cached raw datasets. Loading from disk...")
        aq_df = pd.read_parquet(aq_raw_path)
        w_df = pd.read_parquet(w_raw_path)
    else:
        logger.info("Step 2a: Ingesting Air Quality data from Open-Meteo CAMS for %d neighborhoods...", len(neighborhoods))
        aq_df = fetch_all_air_quality(neighborhoods, diwali_windows, output_dir=raw_dir)
        logger.info("Step 2b: Ingesting Weather data from Open-Meteo Reanalysis...")
        w_df = fetch_all_weather(neighborhoods, diwali_windows, output_dir=raw_dir)

    # 4. Physical Validation & Cleaning
    logger.info("Step 3: Merging Air Quality and Weather records...")
    merged_df = merge_air_quality_and_weather(aq_df, w_df, output_dir=proc_dir)

    logger.info("Step 4: Validating geographic coordinates & physical bounds...")
    coord_valid_df, coord_stats = validate_coordinates(merged_df)
    phys_valid_df, phys_stats = validate_physical_consistency(coord_valid_df)
    dedup_df, dup_removed = remove_duplicates_and_sort(phys_valid_df)

    logger.info("Step 5: Statistical outlier capping and interpolation...")
    capped_df = detect_and_cap_outliers(dedup_df, columns=["pm2_5", "pm10", "temperature_2m", "wind_speed_10m"])
    clean_df = impute_missing_data(capped_df)

    # 5. Feature Engineering
    logger.info("Step 6: Executing complete feature engineering pipeline...")
    feat_df = engineer_all_features(clean_df)

    # 6. Multi-Horizon Targets
    logger.info("Step 7: Synthesizing multi-horizon forward targets (%s)...", horizons)
    dataset_df = create_multi_horizon_targets(feat_df, target_cols=["pm2_5", "pm10"], horizons=horizons)
    dataset_path = os.path.join(proc_dir, "engineered_dataset.parquet")
    dataset_df.to_parquet(dataset_path, index=False)
    logger.info("Saved complete engineered dataset: %d rows x %d columns to %s", len(dataset_df), len(dataset_df.columns), dataset_path)

    # 7. Dataset Builder (Chronological Splits, Spatial Holdouts, Scalers, Data Quality Report)
    logger.info("Step 8: Partitioning datasets, fitting scalers, and generating quality report...")
    report = build_and_save_datasets(
        df=dataset_df,
        neighborhoods=neighborhoods,
        train_years=train_cfg["split"]["train_years"],
        val_years=train_cfg["split"]["val_years"],
        test_years=train_cfg["split"]["test_years"],
        holdout_neighborhoods=train_cfg["split"]["spatial_holdout_neighborhoods"],
        horizons=horizons,
        processed_dir=proc_dir,
        features_dir=feat_dir,
        scalers_dir=scalers_dir,
        reports_dir=reports_dir,
    )

    logger.info("==================================================")
    logger.info("   AEROS DATA PIPELINE COMPLETED SUCCESSFULLY!    ")
    logger.info("   Total Records: %d                              ", report["total_records_collected"])
    logger.info("   Train Records: %d, Val: %d, Test: %d           ", 
                report["dataset_splits"]["train_records"],
                report["dataset_splits"]["val_records"],
                report["dataset_splits"]["test_records"])
    logger.info("   Engineered Features: %d                        ", report["feature_summary"]["total_engineered_features"])
    logger.info("==================================================")


if __name__ == "__main__":
    force = "--force" in sys.argv
    run_pipeline(force_download=force)
