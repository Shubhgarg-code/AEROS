# AEROS: Atmospheric Environmental Risk and Observation System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/React-19.0+-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-3178c6.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-527D75.svg)](https://tailwindcss.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.15+-ee4c2c.svg)](https://pytorch.org/)
[![PyG](https://img.shields.io/badge/PyG-2.8+-3C2179.svg)](https://pyg.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-67%20passed-success.svg)](https://github.com/)

AEROS (**Atmospheric Environmental Risk and Observation System**) is a 100% software-based AI/ML atmospheric intelligence engine and environmental digital twin engineered to analyze, forecast, and simulate episodic air quality extremes before, during, and after Diwali at neighborhood-level spatial resolution across Delhi NCR.

---

## 1. Project Introduction

### 1.1 Objective & Problem Statement
During the post-monsoon onset of winter (late October to mid-November), the National Capital Region (NCR) of Delhi experiences acute, hazardous air pollution episodes. This crisis stems from a compounding confluence of:
1. **Pyrotechnic Emission Surges**: Concentrated, short-duration emissions of fine particulate matter ($\text{PM}_{2.5}, \text{PM}_{10}$), sulfur dioxide ($\text{SO}_2$), and heavy metal aerosols during Diwali night.
2. **Atmospheric Thermal Inversion**: Rapid nocturnal radiative cooling drops the Planetary Boundary Layer (PBL) height from $>1500\,\text{m}$ during the day to $<100\,\text{m}$ at night, creating an atmospheric "lid" that traps pollutants near ground level.
3. **Calm Winds & Stagnation**: Extremely low surface wind speeds ($<1.5\,\text{m/s}$) prevent horizontal dispersion, interspersed with regional northwesterly winds that transport agricultural biomass burning plumes into Delhi.
4. **Intra-Urban Micro-Heterogeneity**: Road density, traffic bottlenecks (e.g., Anand Vihar, ITO), industrial clusters (e.g., Bawana, Okhla), and green buffer zones (e.g., Lodhi Road, Siri Fort) cause marked variation in pollution exposure across neighborhoods.

### 1.2 Core Capabilities
- **Multi-Horizon Temporal Forecasting**: Predicts future $\text{PM}_{2.5}$ and $\text{PM}_{10}$ across 7 lead horizons ($1\text{h}, 3\text{h}, 6\text{h}, 12\text{h}, 24\text{h}, 48\text{h}, 72\text{h}$) with conformal uncertainty bounds.
- **Geospatial Neighborhood Prediction**: Estimates pollution at unmonitored coordinates using spatial graph representations (GCN, GAT, GraphSAGE, ST-GNN), Haversine proximity, land use, and road density.
- **Dynamic Advection-Diffusion Propagation**: Models 2D physical transport across a 121-cell spatial grid using upwind finite difference schemes, wind velocity decomposition, and adaptive CFL sub-stepping.
- **Counterfactual Diwali What-If Simulation**: Simulates 7 distinct policy and environmental scenarios (firecracker ban compliance, traffic curbs, synoptic flushing).
- **Atmospheric Recovery Prediction**: Computes clearance times ($T_{\text{clear}}$) required for particulate concentrations to fall below statutory National Ambient Air Quality Standards (NAAQS: $60\,\mu\text{g/m}^3$ for $\text{PM}_{2.5}$, $100\,\mu\text{g/m}^3$ for $\text{PM}_{10}$) with 90% conformal prediction intervals.
- **Minimal, Human, Calm Environmental Intelligence Interface**: Thoughtfully designed light-first frontend (React 19, TypeScript, Tailwind CSS, Recharts, Leaflet with CartoDB Positron) inspired by Linear, Apple, and Stripe design principles.

---

## 2. Interactive Frontend & Digital Twin (Round 7 — UI Refinement)

AEROS features a thoughtfully crafted, human-centred, light-first environmental intelligence platform:
- **Colour System**: Warm off-white canvas (`#F7F7F3`), charcoal typography (`#202A30`), muted environmental green accent (`#527D75`), soft atmospheric blue (`#7899B5`), and clean white cards (`#FFFFFF`) with subtle warm grey borders (`#E5E5DF`).
- **Human-Centred Environmental Communication**: Clear, contextual environmental briefings accompany every chart and metric (e.g. *"Citywide pollution is currently Moderate (AQI 151). Stagnant northwesterly winds (2.5 m/s) and nocturnal thermal inversion are trapping particulates across Delhi NCR"*).
- **Geospatial Map Experience**: CartoDB Positron light tile basemap with clean station pins, accessible categorical pollution indicators, and discrete 121-cell mesh overlays.
- **Scientific Restraint**: Clean line charts with subtle gridlines, 90% conformal confidence envelopes, and transparent model boundaries.

### 2.1 The 9 Core Application Modules

| Module Page | Description | Primary Backend API |
| :--- | :--- | :--- |
| **1. Overview** | Real-time ambient conditions, atmospheric narrative briefing, weather factors, 24h diurnal cycle, and 15 physical CAAQMS station table. | `GET /overview` |
| **2. Environmental Map** | Clean CartoDB Positron basemap with 15 physical station pins, 121-cell discrete mesh overlay, and fine vs. coarse particulate toggles. | `GET /stations`, `GET /geojson/grid` |
| **3. Air Quality Forecasts** | Multi-horizon predictions ($1\text{h} \dots 72\text{h}$) for any station, featuring 90% conformal uncertainty envelopes and key environmental drivers. | `POST /predict/air-quality` |
| **4. Neighbourhood Estimates** | Landmark presets and arbitrary coordinate estimation comparing GraphSAGE GNN, inverse distance weighting, and spatial gradient boosting. | `POST /predict/spatial` |
| **5. Pollution Propagation** | Interactive 2D advection-diffusion fluid transport player with play/pause/step controls across an 11×11 discrete grid and mass conservation diagnostics. | `POST /simulate/propagation` |
| **6. What-if Scenarios** | Counterfactual policy simulator evaluating 7 policy interventions (firecracker ban, odd-even vehicle rationing, weather flushing) with before-and-after curves. | `POST /simulate/scenario` |
| **7. Air Quality Recovery** | Relaxation engine computing clearance hours ($T_{\text{clear}}$) below statutory NAAQS standards ($60\,\mu\text{g/m}^3$), unreached threshold handling, and wind sensitivity spectrum. | `POST /predict/recovery` |
| **8. Scenario Comparison** | Side-by-side benchmark matrix and horizontal bar comparison ranking policy options by cumulative exposure avoided. | `POST /compare/scenarios` |
| **9. Model Intelligence** | Technical transparency page showing real test MAE, RMSE, and $R^2$ on held-out stations and test seasons, numerical PDE solver specifications, and documented boundaries. | `GET /models/metadata`, `GET /simulation/health` |

---

## 3. Technology Stack

- **Frontend Platform**: React 19, TypeScript 5.7, Tailwind CSS 3.4, Vite 6.2, Lucide Icons
- **Data Visualization & GIS**: Recharts 2.15, Leaflet 1.9 (CartoDB Positron Light Tiles), GeoJSON
- **Backend & Inference**: FastAPI 0.139, Uvicorn 0.51, Pydantic 2.12
- **Deep Learning & Graph Neural Networks**: PyTorch 2.15+, PyTorch Geometric 2.8+, XGBoost 3.4+, Scikit-learn 1.9+
- **Physics Solvers**: Finite-Difference Upwind Differencing, SciPy 1.17+, NumPy 2.4+
- **Verification & Testing**: Pytest 9.1+ (**67/67 unit and integration tests passing with 100% success**)

---

## 4. Production API Endpoints (`aeros/api/`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/overview` | Citywide PM2.5/PM10, AQI, weather conditions, active alerts, and 15 station readings. |
| `GET` | `/stations` | Full list of CAAQMS physical monitoring stations with coordinates and road density factors. |
| `GET` | `/geojson/grid` | GeoJSON polygon layer for the 121-cell discrete geographical grid. |
| `GET` | `/geojson/heatmap` | Spatial PM2.5/PM10 heatmap GeoJSON layer. |
| `POST` | `/predict/air-quality` | Multi-horizon temporal forecast ($1\text{h} - 72\text{h}$) with conformal intervals and feature importance. |
| `POST` | `/predict/spatial` | Neighborhood estimation comparing GNN, IDW, and XGBoost with supporting station anchors. |
| `POST` | `/simulate/propagation` | 2D advection-diffusion fluid transport rollout with hourly snapshot grids. |
| `POST` | `/simulate/scenario` | Counterfactual policy scenario rollout (firecracker ban compliance, traffic curbs). |
| `POST` | `/compare/scenarios` | Side-by-side benchmarking of all scenarios against business-as-usual baseline. |
| `POST` | `/predict/recovery` | Estimates clearance hours ($T_{\text{clear}}$), 90% conformal intervals, and wind sensitivity. |
| `GET` | `/models/metadata` | Real holdout benchmarks (MAE, RMSE, $R^2$), grid specs, and documented limitations. |
| `GET` | `/simulation/health` | Service diagnostics, physics solver configuration, and scenario registry. |

---

## 5. Execution Instructions

### 5.1 Run the Python Test Suite (67 Tests)
```bash
python -m pytest aeros/tests -v
```

### 5.2 Start the Backend API Server
```bash
python -m uvicorn aeros.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation: `http://localhost:8000/docs`.

### 5.3 Start the Interactive Frontend Application
```bash
cd frontend
npm run dev
```
Open your browser at `http://localhost:3000` to interact with the AEROS environmental intelligence digital twin.

*(Alternatively, the built production frontend is also mounted on FastAPI at `http://localhost:8000/dashboard/`)*.

### 5.4 Build Frontend for Production
```bash
cd frontend
npm run build
```

---

## 6. Development Status Tracker

- [x] **Round 1: Research, Environmental Physics & System Architecture**
- [x] **Round 2: Data Engineering & Validation Pipeline (39,600 observations across 5 Diwali windows)**
- [x] **Round 3: Multi-Horizon Temporal Forecasting (XGBoost, LSTM, GRU, Transformer, Ensemble)**
- [x] **Round 4: Spatial Intelligence & Graph Neural Networks (121-cell Grid, GCN, GAT, GraphSAGE, ST-GNN)**
- [x] **Round 5: Atmospheric Simulation, Scenario Intelligence & Recovery (2D PDE Upwind Solver, 7 Scenarios)**
- [x] **Round 7: Interactive Frontend, Environmental Digital Twin & Data Visualization**
  - Minimal, human, calm, light-first environmental design system (React 19 + TypeScript + Tailwind CSS).
  - 9 integrated operational modules (Overview, Environmental Map, Air Quality Forecasts, Neighbourhood Estimates, Pollution Propagation, What-if Scenarios, Air Quality Recovery, Scenario Comparison, Model Intelligence).
  - Leaflet geospatial map with CartoDB Positron light tiles, 121-cell mesh, and physical station pins.
  - Multi-horizon forecast viewer with 90% conformal uncertainty bands and feature attribution.
  - Counterfactual Diwali simulator with side-by-side before-and-after timelines and mandatory scientific disclaimer.
  - Atmospheric recovery viewer with unreached threshold handling and synoptic ventilation sensitivity spectrum.
  - **67/67 Unit & Integration Tests Passing (100% test pass rate).**
