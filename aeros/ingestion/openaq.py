"""OpenAQ API v3 Ingestion Module for AEROS.

Provides integration with OpenAQ REST API v3 for ambient air quality monitoring,
with API key support from environment variables and test fixture mock generation.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import requests

logger = logging.getLogger("aeros.ingestion.openaq")

OPENAQ_BASE_URL = "https://api.openaq.org/v3"


class OpenAQClient:
    """Client for OpenAQ API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAQ_API_KEY", "")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})

    def get_locations(self, city: str = "Delhi", limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch active monitoring locations for a city."""
        url = f"{OPENAQ_BASE_URL}/locations"
        params = {"city": city, "limit": limit}

        try:
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                logger.info("Retrieved %d OpenAQ locations for %s", len(results), city)
                return results
            elif resp.status_code == 401 or resp.status_code == 403:
                logger.warning("OpenAQ API requires valid API key (Status %d)", resp.status_code)
                return []
            else:
                logger.warning("OpenAQ request failed with status %d: %s", resp.status_code, resp.text[:100])
                return []
        except Exception as e:
            logger.warning("Failed to connect to OpenAQ API: %s", e)
            return []

    def get_measurements(
        self,
        location_id: int,
        date_from: str,
        date_to: str,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Fetch measurements for a specific location within a date range."""
        url = f"{OPENAQ_BASE_URL}/locations/{location_id}/measurements"
        params = {"date_from": date_from, "date_to": date_to, "limit": limit}

        try:
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("results", [])
                if not records:
                    return pd.DataFrame()
                df = pd.json_normalize(records)
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.warning("OpenAQ measurements fetch failed for location %s: %s", location_id, e)
            return pd.DataFrame()


def generate_openaq_test_fixture(
    num_samples: int = 24,
    neighborhood_id: str = "anand_vihar",
) -> pd.DataFrame:
    """Generates synthetic unit test fixture conforming to OpenAQ observation schema."""
    timestamps = pd.date_range("2024-11-01 00:00:00", periods=num_samples, freq="h")
    data = {
        "timestamp": timestamps,
        "neighborhood_id": neighborhood_id,
        "pm2_5": [120.0 + i * 2.5 for i in range(num_samples)],
        "pm10": [220.0 + i * 4.0 for i in range(num_samples)],
        "source": "OpenAQ_Fixture",
    }
    return pd.DataFrame(data)
