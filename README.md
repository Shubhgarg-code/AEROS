# AEROS 🌍
### AI-Powered Enavironmental Reconstruction And Optimization System

**Predict. Understand. Prevent.**

AEROS is a software-based AI/ML platform designed to predict air pollution before, during, and after Diwali. It uses historical air-quality data, meteorological conditions, geographical information, and deep learning to forecast pollution patterns at neighborhood level.

The platform aims to transform environmental data into meaningful predictions and actionable insights.

---

## 🎯 Problem Statement

Air pollution during Diwali is a major environmental concern. Existing monitoring systems rely on a limited number of physical monitoring stations, making it difficult to understand pollution variations across individual neighborhoods.

AEROS aims to address this limitation through AI-powered forecasting, spatial prediction, and pollution scenario simulation.

## 💡 Our Solution

AEROS combines machine learning, deep learning, and geospatial analysis to:

- Predict future PM2.5 and PM10 concentrations.
- Estimate air quality in areas without monitoring stations.
- Analyze pollution patterns across neighborhoods.
- Predict possible pollution movement.
- Simulate alternative Diwali emission scenarios.
- Estimate pollution recovery time.
- Generate data-driven pollution mitigation recommendations.

## 🚀 Core Features

| Feature | Description |
|---|---|
| Air Quality Forecasting | Predicts future PM2.5 and PM10 levels. |
| Virtual Pollution Sensors | Estimates pollution in unmonitored locations. |
| Spatial Intelligence | Analyzes pollution patterns across neighborhoods. |
| Pollution Propagation | Models possible movement of pollution. |
| Diwali Simulator | Compares different hypothetical emission scenarios. |
| Recovery Prediction | Estimates when pollution may return below a selected threshold. |
| Mitigation Intelligence | Identifies potential pollution reduction strategies. |

## 🧠 AI/ML Technologies

The project explores the following techniques:

- LSTM and GRU Networks
- Transformer-based Time Series Forecasting
- Graph Neural Networks (GNN)
- Spatiotemporal Deep Learning
- Physics-Informed Machine Learning
- XGBoost
- Spatial Interpolation
- Uncertainty Quantification
- Explainable AI

The final model architecture will be selected based on dataset availability and actual evaluation performance.

## 📊 Data Sources

AEROS is designed to work with publicly available environmental datasets and APIs.

| Source | Purpose |
|---|---|
| CPCB | Historical air-quality observations |
| OpenAQ | Air-quality monitoring data |
| Open-Meteo | Weather information |
| ERA5 | Historical atmospheric data |
| OpenStreetMap | Roads and geographical information |
| NASA Earth Observation | Environmental indicators |
| NASA FIRMS | Fire and thermal anomaly information |

Data availability, geographical coverage, and historical completeness will be verified during development.

## ⚙️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Machine Learning | Scikit-learn, XGBoost |
| Deep Learning | PyTorch |
| Graph Learning | PyTorch Geometric |
| Data Processing | Pandas, NumPy |
| Geospatial Analysis | GeoPandas, Rasterio |
| Backend | FastAPI |
| Database | PostgreSQL + PostGIS |
| Frontend | React / Next.js |
| Visualization | Mapbox / deck.gl |
| Experiment Tracking | MLflow |

## 🏗️ System Architecture

```text
        ENVIRONMENTAL DATA SOURCES
                   |
                   v
          DATA COLLECTION
                   |
                   v
        DATA PREPROCESSING
                   |
                   v
          FEATURE ENGINEERING
                   |
                   v
             AI/ML ENGINE
                   |
          +--------+--------+
          |        |        |
          v        v        v
       TEMPORAL  SPATIAL  SCENARIO
       FORECAST  MODEL    SIMULATION
          |        |        |
          +--------+--------+
                   |
                   v
          PREDICTION ENGINE
                   |
                   v
          FASTAPI BACKEND
                   |
                   v
          AEROS WEB PLATFORM
```

## 📁 Project Structure

```text
AEROS/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── features/
│   └── external/
│
├── ingestion/
│
├── preprocessing/
│
├── models/
│
├── training/
│
├── simulation/
│
├── optimization/
│
├── inference/
│
├── api/
│
├── configs/
│
├── artifacts/
│
├── reports/
│
├── tests/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

*The directory structure will evolve as development progresses.*

## 💻 Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AEROS
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file using `.env.example`.

Add the required API credentials and configuration values.

Never commit API keys or private credentials to GitHub.

## ▶️ Running the Project

The following commands are planned for the data and model pipeline. They will become executable as the respective modules are implemented.

```bash
# Collect environmental data
python -m ingestion.main

# Clean and preprocess data
python -m preprocessing.cleaning

# Generate features
python -m preprocessing.features

# Build training datasets
python -m preprocessing.dataset_builder

# Train the forecasting model
python -m training.train

# Evaluate model performance
python -m training.evaluate

# Start the API
uvicorn api.main:app --reload
```

## 📈 Model Evaluation

Model performance will be evaluated using:

- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- R² Score
- Forecast horizon-specific errors
- Spatial prediction errors
- Prediction uncertainty

Models will be compared against baseline forecasting methods.

Actual evaluation results will be published here after training and validation.

## 🔒 Project Scope

AEROS is a completely software-based project.

It does not require:

- Physical air-quality sensors
- Arduino or Raspberry Pi
- IoT hardware
- Drones
- Physical monitoring installations

The system relies on existing datasets, APIs, computational models, and software-based simulations.

## ⚠️ Limitations

- Prediction accuracy depends on the quality and availability of historical data.
- Neighborhood-level predictions may have higher uncertainty in areas with limited monitoring coverage.
- Hypothetical scenario simulations are not equivalent to measured real-world pollution reductions.
- Satellite observations do not directly provide continuous neighborhood-level PM2.5 measurements.
- Model performance must be independently evaluated before deployment.

## 👥 Team

Developed as a collaborative student-led AI/ML project.

**Project:** AEROS  
**Domain:** Artificial Intelligence, Machine Learning, Environmental Technology  
**Focus:** Air Pollution Prediction and Environmental Intelligence

## 📜 License

License information will be added when the project licensing decision is finalized.

---

**AEROS — Turning Environmental Data into Predictive Intelligence.**
