"""Weather and Meteorological Ingestion Module for AEROS.

Fetches real hourly meteorological reanalysis data from Open-Meteo Historical
Archive API.
Variables: Temperature, Relative Humidity, Surface Pressure, Wind Speed, Wind
Direction, Precipitation.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import requests

logger = logging.getLogger("aeros.ingestion.weather")
logging.basicConfig(level=logging.INFO)

ARCHIVE_API_ENDPOINT = "https://archive-api.open-meteo.com/v1/archive"


def fetch_neighborhood_weather(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    neighborhood_id: str,
    hourly_vars: Optional[List[str]] = None,
    max_retries: int = 3,
    backoff_seconds: float = 1.5,
) -> pd.DataFrame:
    """Fetch hourly weather variables for a neighborhood coordinate."""
    if hourly_vars is None:
        hourly_vars = [
            "temperature_2m",
            "relative_humidity_2m",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
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
            resp = requests.get(ARCHIVE_API_ENDPOINT, params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                hourly = data.get("hourly", {})
                if not hourly or "time" not in hourly:
                    raise ValueError(
                        f"Empty hourly payload from Open-Meteo Weather for {neighborhood_id}"
                    )

                df = pd.DataFrame(hourly)
                df["timestamp"] = pd.to_datetime(df["time"])
                df.drop(columns=["time"], inplace=True)
                df["neighborhood_id"] = neighborhood_id
                logger.info(
                    "Fetched %d weather records for %s [%s to %s]",
                    len(df),
                    neighborhood_id,
                    start_date,
                    end_date,
                )
                return df
            else:
                logger.warning(
                    "Open-Meteo Weather returned status %d: %s (attempt %d/%d)",
                    resp.status_code,
                    resp.text[:100],
                    attempt + 1,
                    max_retries,
                )
        except Exception as e:
            last_exc = e
            logger.warning(
                "Weather request failed for %s (attempt %d/%d): %s",
                neighborhood_id,
                attempt + 1,
                max_retries,
                e,
            )
        time.sleep(backoff_seconds * (attempt + 1))

    raise RuntimeError(
        f"Failed to fetch weather for {neighborhood_id} after {max_retries} attempts: {last_exc}"
    )


def fetch_all_weather(
    neighborhoods: List[Dict[str, Any]],
    diwali_windows: List[Dict[str, Any]],
    output_dir: str = "aeros/data/raw",
) -> pd.DataFrame:
    """Fetch weather across all configured neighborhoods and Diwali windows."""
    os.makedirs(output_dir, exist_ok=True)
    all_frames = []

    for window in diwali_windows:
        year = window["year"]
        start_date = window["start_date"]
        end_date = window["end_date"]
        logger.info(
            "--- Fetching Weather for Window %d (%s to %s) ---",
            year,
            start_date,
            end_date,
        )

        for nh in neighborhoods:
            nh_id = nh["id"]
            lat = nh["latitude"]
            lon = nh["longitude"]
            df_w = fetch_neighborhood_weather(
                lat=lat,
                lon=lon,
                start_date=start_date,
                end_date=end_date,
                neighborhood_id=nh_id,
            )
            df_w["diwali_year"] = year
            all_frames.append(df_w)
            time.sleep(0.15)  # Politeness interval

    combined_df = pd.concat(all_frames, ignore_index=True)
    combined_path = os.path.join(output_dir, "weather_raw.parquet")
    combined_df.to_parquet(combined_path, index=False)
    logger.info(
        "Successfully saved total %d weather rows to %s",
        len(combined_df),
        combined_path,
    )
    return combined_df
