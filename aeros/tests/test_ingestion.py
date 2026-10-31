"""Unit tests for AEROS Data Ingestion Modules."""

import pandas as pd
import pytest

from aeros.ingestion.cpcb import get_cpcb_stations
from aeros.ingestion.openaq import OpenAQClient, generate_openaq_test_fixture


def test_cpcb_station_metadata():
    """Verify CPCB CAAQMS station registry contains all required keys and valid coordinates."""
    stations = get_cpcb_stations()
    assert len(stations) >= 15
    for st in stations:
        assert "station_id" in st
        assert "neighborhood_id" in st
        assert "latitude" in st
        assert "longitude" in st
        assert 28.0 <= st["latitude"] <= 29.0
        assert 76.5 <= st["longitude"] <= 77.6


def test_openaq_fixture_generator():
    """Verify OpenAQ synthetic fixture format matches expected ingestion schema."""
    fixture_df = generate_openaq_test_fixture(num_samples=48, neighborhood_id="anand_vihar")
    assert len(fixture_df) == 48
    assert "pm2_5" in fixture_df.columns
    assert "pm10" in fixture_df.columns
    assert "timestamp" in fixture_df.columns
    assert fixture_df["pm2_5"].min() > 0.0


def test_openaq_client_unauthorized_handling():
    """Verify OpenAQ client handles unauthenticated requests without throwing unhandled exceptions."""
    client = OpenAQClient(api_key="invalid_test_key")
    locations = client.get_locations(city="Delhi", limit=2)
    assert isinstance(locations, list)
