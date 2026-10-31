# AEROS Data Quality & Hygiene Report

**Generated At**: 2026-10-31T23:58:33.120801  
**System**: Atmospheric Environmental Risk and Observation System (AEROS)  
**Target Domain**: Delhi NCR, India (15 Benchmark Neighborhoods)

---

## 1. Executive Summary
- **Total Ingested Records**: 38,520
- **Monitoring Stations**: 15 stations
- **Temporal Span**: 2021-10-25 00:00:00 to 2025-10-28 23:00:00
- **Historical Diwali Periods**: [2021, 2022, 2023, 2024, 2025]
- **Total Engineered Features**: 72
- **Data Completeness**: 100.0% (Zero unhandled missing values)

---

## 2. Chronological & Spatial Partitioning
The dataset is partitioned to rigorously prevent temporal lookahead leakage and evaluate spatial generalization to unmonitored neighborhoods:

| Split | Years | Record Count | Percentage |
| :--- | :--- | :--- | :--- |
| **Training Split** | [2021, 2022, 2023] | 23,760 | 61.7% |
| **Validation Split** | [2024] | 7,920 | 20.6% |
| **Test Split (Held-out Future)** | [2025] | 6,840 | 17.8% |

### Spatial Generalization Holdout
- **Monitored Training Locations (12)**: Anand Vihar, Punjabi Bagh, RK Puram, ITO, Bawana, Narela, Lodhi Road, Okhla Phase 2, Rohini, Wazirpur, Siri Fort, Connaught Place.
- **Unseen Holdout Locations (3)**: dwarka, jahangirpuri, mandir_marg.

---

## 3. Atmospheric Target Distributions ($\mu g/m^3$)

| Pollutant Target | Mean | Std | Min | Median | 75th %ile | 95th %ile (Diwali Surge) | Max |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$PM_{2.5}$** | 94.92 | 42.4 | 25.4 | 78.1 | 116.4 | 177.0 | 298.41 |
| **$PM_{10}$** | 159.97 | 65.88 | 38.8 | 143.0 | 194.6 | 286.8 | 459.89 |

*Observation*: The 95th percentile and maximum values reflect severe pyrotechnic pulse emissions and stagnation during Diwali peak night windows.

---

## 4. Ingestion Data Sources & Provenance
1. **Air Quality Observations**: CPCB continuous ambient air quality network cross-referenced with Open-Meteo Copernicus CAMS hourly reanalysis.
2. **Atmospheric Meteorology**: Open-Meteo Reanalysis (Surface Temperature, Relative Humidity, Pressure, Wind Vectors $u, v$, Stagnation Index).
3. **Geospatial & Road Topology**: OpenStreetMap road network density, arterial highway proximity, and land-use classifications.

---

## 5. Feature Engineering Inventory (72 features)
Features are organized into:
- **Temporal & Solar Cycles**: `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`, `doy_sin`, `doy_cos`
- **Diwali Proximity**: `hours_to_diwali`, `diwali_surge_intensity`
- **Meteorological & Transport**: `temperature_2m`, `relative_humidity_2m`, `surface_pressure`, `wind_speed`, `wind_u`, `wind_v`, `wind_dir_sin`, `wind_dir_cos`, `stagnation_index`, `dispersion_capacity`
- **Autoregressive Lags**: $PM_{2.5}$ and $PM_{10}$ at $t-1, t-2, t-3, t-6, t-12, t-24$ hours
- **Rolling Statistics**: 6h, 12h, 24h rolling means and standard deviations
- **Spatial Built-Environment**: Latitude, Longitude, Road Density Factor, Population Density Factor
