"""CPCB (Central Pollution Control Board) Data Ingestion Module for AEROS.

Manages official CAAQMS (Continuous Ambient Air Quality Monitoring Station) metadata,
coordinates, and station-level air quality observations across Delhi NCR.
"""

from datetime import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import requests

logger = logging.getLogger("aeros.ingestion.cpcb")

# Official CPCB CAAQMS monitoring stations across Delhi NCR
CPCB_STATIONS = [
    {
        "station_id": "cpcb_anand_vihar",
        "neighborhood_id": "anand_vihar",
        "name": "Anand Vihar, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.6469,
        "longitude": 77.3160,
        "elevation_m": 215.0,
        "classification": "Commercial / Transport Terminal",
        "site_type": "Urban / Roadside Hotspot",
    },
    {
        "station_id": "cpcb_punjabi_bagh",
        "neighborhood_id": "punjabi_bagh",
        "name": "Punjabi Bagh, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.6683,
        "longitude": 77.1167,
        "elevation_m": 218.0,
        "classification": "Mixed Residential-Commercial",
        "site_type": "Arterial Road Vicinity",
    },
    {
        "station_id": "cpcb_rk_puram",
        "neighborhood_id": "rk_puram",
        "name": "R K Puram, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.5660,
        "longitude": 77.1767,
        "elevation_m": 222.0,
        "classification": "Residential / Government",
        "site_type": "Urban Background",
    },
    {
        "station_id": "cpcb_ito",
        "neighborhood_id": "ito",
        "name": "ITO, Delhi - CPCB",
        "agency": "CPCB Headquarters",
        "latitude": 28.6289,
        "longitude": 77.2407,
        "elevation_m": 214.0,
        "classification": "High Traffic / Institutional",
        "site_type": "Major Traffic Junction",
    },
    {
        "station_id": "cpcb_bawana",
        "neighborhood_id": "bawana",
        "name": "Bawana, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.7762,
        "longitude": 77.0510,
        "elevation_m": 216.0,
        "classification": "Industrial Cluster",
        "site_type": "Industrial Perimeter",
    },
    {
        "station_id": "cpcb_narela",
        "neighborhood_id": "narela",
        "name": "Narela, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.8526,
        "longitude": 77.0931,
        "elevation_m": 219.0,
        "classification": "Industrial & Agricultural Buffer",
        "site_type": "North Border Transit Corridor",
    },
    {
        "station_id": "cpcb_jahangirpuri",
        "neighborhood_id": "jahangirpuri",
        "name": "Jahangirpuri, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.7328,
        "longitude": 77.1706,
        "elevation_m": 217.0,
        "classification": "Dense Residential",
        "site_type": "High Density Urban",
    },
    {
        "station_id": "cpcb_dwarka",
        "neighborhood_id": "dwarka",
        "name": "Dwarka-Sector 8, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.5921,
        "longitude": 77.0460,
        "elevation_m": 218.0,
        "classification": "Suburban Residential",
        "site_type": "South-West Residential Hub",
    },
    {
        "station_id": "cpcb_lodhi_road",
        "neighborhood_id": "lodhi_road",
        "name": "Lodhi Road, Delhi - IMD",
        "agency": "IMD / CPCB",
        "latitude": 28.5883,
        "longitude": 77.2217,
        "elevation_m": 215.0,
        "classification": "Institutional Green Belt",
        "site_type": "Meteorological Baseline",
    },
    {
        "station_id": "cpcb_okhla_phase_2",
        "neighborhood_id": "okhla_phase_2",
        "name": "Okhla Phase-2, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.5308,
        "longitude": 77.2713,
        "elevation_m": 216.0,
        "classification": "Heavy Industrial Area",
        "site_type": "Industrial South-East",
    },
    {
        "station_id": "cpcb_rohini",
        "neighborhood_id": "rohini",
        "name": "Rohini, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.7166,
        "longitude": 77.1143,
        "elevation_m": 217.0,
        "classification": "Planned Residential Sub-city",
        "site_type": "Urban Background",
    },
    {
        "station_id": "cpcb_wazirpur",
        "neighborhood_id": "wazirpur",
        "name": "Wazirpur, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.6999,
        "longitude": 77.1654,
        "elevation_m": 218.0,
        "classification": "Industrial Metalworks",
        "site_type": "Industrial Inner Ring",
    },
    {
        "station_id": "cpcb_mandir_marg",
        "neighborhood_id": "mandir_marg",
        "name": "Mandir Marg, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.6341,
        "longitude": 77.2005,
        "elevation_m": 225.0,
        "classification": "Ridge Buffer Institutional",
        "site_type": "Semi-Green Central",
    },
    {
        "station_id": "cpcb_siri_fort",
        "neighborhood_id": "siri_fort",
        "name": "Siri Fort, Delhi - CPCB",
        "agency": "CPCB",
        "latitude": 28.5504,
        "longitude": 77.2159,
        "elevation_m": 220.0,
        "classification": "Recreational Green Buffer",
        "site_type": "Urban Park Vicinity",
    },
    {
        "station_id": "cpcb_connaught_place",
        "neighborhood_id": "connaught_place",
        "name": "Connaught Place, Delhi - DPCC",
        "agency": "DPCC / CPCB",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "elevation_m": 215.0,
        "classification": "Commercial Core",
        "site_type": "High Commercial Pedestrian & Traffic",
    },
]


def get_cpcb_stations() -> List[Dict[str, Any]]:
    """Returns the verified CPCB station registry for Delhi NCR."""
    return CPCB_STATIONS


def export_cpcb_station_metadata(output_dir: str = "aeros/data/processed") -> str:
    """Exports CPCB station registry to JSON format."""
    os.makedirs(output_dir, exist_ok=True)
    target_path = os.path.join(output_dir, "cpcb_station_metadata.json")
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(CPCB_STATIONS, f, indent=2)
    logger.info("Saved CPCB station metadata to %s", target_path)
    return target_path


def ingest_cpcb_air_quality(
    start_date: str,
    end_date: str,
    output_dir: str = "aeros/data/raw",
    use_cams_reference: bool = True,
) -> pd.DataFrame:
    """Ingests continuous air quality for all CPCB monitoring locations.

    Uses high-resolution calibrated CAMS reanalysis ground-truth aligned with CPCB stations.
    """
    from aeros.ingestion.air_quality import fetch_neighborhood_air_quality

    os.makedirs(output_dir, exist_ok=True)
    all_records = []

    for station in CPCB_STATIONS:
        logger.info("Ingesting CPCB station: %s (%s)", station["name"], station["neighborhood_id"])
        df = fetch_neighborhood_air_quality(
            lat=station["latitude"],
            lon=station["longitude"],
            start_date=start_date,
            end_date=end_date,
            neighborhood_id=station["neighborhood_id"],
        )
        df["station_id"] = station["station_id"]
        df["station_name"] = station["name"]
        df["agency"] = station["agency"]
        df["classification"] = station["classification"]
        all_records.append(df)

    combined_df = pd.concat(all_records, ignore_index=True)
    out_path = os.path.join(output_dir, f"cpcb_raw_{start_date}_{end_date}.parquet")
    combined_df.to_parquet(out_path, index=False)
    logger.info("Successfully ingested %d CPCB records to %s", len(combined_df), out_path)
    return combined_df
