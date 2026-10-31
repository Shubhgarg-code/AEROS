"""Air Quality Ingestion Module for AEROS.

Fetches real atmospheric air quality measurements (PM2.5, PM10, NO2, SO2,
O3, AOD)
from the Open-Meteo Air Quality CAMS reanalysis API across defined Diwali
windows.
"""

from datetime import datetime
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import requests

logger = logging.getLogger("aeros.ingestion.air_quality")
logging.basicConfig(level=logging.INFO)

API_ENDPOINT = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_neighborhood_air_quality(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    neighborhood_id: str,
    hourly_vars: Optional[List[str]] = None,
    max_retries: int = 3,
    backoff_seconds: float = 1.5,
) -> pd.DataFrame:
    """Fetch hourly air quality for a single neighborhood coordinate."""
    if hourly_vars is None:
        hourly_vars = [
            "pm10",
            "pm2_5",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "aerosol_optical_depth",
        ]

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(hourly_vars),
        "timezone": "Asia/Kolkata",
    }

    last_exc = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(API_ENDPOINT, params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                hourly = data.get("hourly", {})
                if not hourly or "time" not in hourly:
                    raise ValueError(
                        f"Empty hourly payload from Open-Meteo for {neighborhood_id}"
                    )

                df = pd.DataFrame(hourly)
                df["timestamp"] = pd.to_datetime(df["time"])
                df.drop(columns=["time"], inplace=True)
                df["neighborhood_id"] = neighborhood_id
                df["latitude"] = lat
                df["longitude"] = lon
                logger.info(
                    "Fetched %d air quality records for %s [%s to %s]",
                    len(df),
                    neighborhood_id,
                    start_date,
                    end_date,
                )
                return df
            else:
                logger.warning(
                    "Open-Meteo returned status %d: %s (attempt %d/%d)",
                    resp.status_code,
                    resp.text[:100],
                    attempt + 1,
                    max_retries,
                )
        except Exception as e:
            last_exc = e
            logger.warning(
                "Request failed for %s (attempt %d/%d): %s",
                neighborhood_id,
                attempt + 1,
                max_retries,
                e,
            )
        time.sleep(backoff_seconds * (attempt + 1))

    raise RuntimeError(
        f"Failed to fetch air quality for {neighborhood_id} after {max_retries} attempts: {last_exc}"
    )


def fetch_all_air_quality(
    neighborhoods: List[Dict[str, Any]],
    diwali_windows: List[Dict[str, Any]],
    output_dir: str = "aeros/data/raw",
) -> pd.DataFrame:
    """Fetch air quality across all configured neighborhoods and Diwali windows."""
    os.makedirs(output_dir, exist_ok=True)
    all_frames = []

    for window in diwali_windows:
        year = window["year"]
        start_date = window["start_date"]
        end_date = window["end_date"]
        diwali_date = window["diwali_date"]
        logger.info(
            "--- Processing Diwali Window %d (%s to %s) ---",
            year,
            start_date,
            end_date,
        )

        for nh in neighborhoods:
            nh_id = nh["id"]
            lat = nh["latitude"]
            lon = nh["longitude"]
            df_nh = fetch_neighborhood_air_quality(
                lat=lat,
                lon=lon,
                start_date=start_date,
                end_date=end_date,
                neighborhood_id=nh_id,
            )
            df_nh["diwali_year"] = year
            df_nh["diwali_date"] = pd.to_datetime(diwali_date)
            df_nh["neighborhood_name"] = nh["name"]
            df_nh["land_use"] = nh.get("land_use", "Mixed")
            df_nh["road_density_factor"] = nh.get("road_density_factor", 1.0)
            df_nh["population_density_factor"] = nh.get(
                "population_density_factor", 1.0
            )
            all_frames.append(df_nh)
            time.sleep(0.15)  # Politeness interval

    combined_df = pd.concat(all_frames, ignore_index=True)
    combined_path = os.path.join(output_dir, "air_quality_raw.parquet")
    combined_df.to_parquet(combined_path, index=False)
    csv_sample_path = os.path.join(output_dir, "air_quality_raw_sample.csv")
    combined_df.head(200).to_csv(csv_sample_path, index=False)
    logger.info(
        "Successfully saved total %d air quality rows to %s",
        len(combined_df),
        combined_path,
    )
    return combined_df
