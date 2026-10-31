"""FastAPI Application Entry Point for AEROS.

Atmospheric Environmental Risk and Observation System (AEROS)
REST API Service providing deep-learning inference, spatial graph intelligence,
atmospheric transport simulation, and counterfactual scenario modeling.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from aeros.api.routes import router

app = FastAPI(
    title="AEROS — Atmospheric Environmental Risk and Observation System",
    description=(
        "Software-only AI/ML atmospheric intelligence platform predicting, simulating, "
        "and evaluating air quality and episodic Diwali pollution events across Delhi NCR."
    ),
    version="1.7.0",
)

# Enable CORS for frontend dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount core simulation and inference routes
app.include_router(router, prefix="/api/v1")
app.include_router(router, prefix="/api")
app.include_router(router)  # Also mount at root for direct endpoint access

# Mount frontend web dashboard if built
dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/dashboard", StaticFiles(directory=dist_dir, html=True), name="dashboard")


@app.get("/", summary="Root status check")
def root_status():
    return {
        "service": "AEROS API",
        "version": "1.7.0",
        "status": "ONLINE",
        "documentation": "/docs",
        "endpoints": [
            "/simulate/propagation",
            "/simulate/scenario",
            "/compare/scenarios",
            "/predict/recovery",
            "/predict/neighborhood",
            "/simulation/health",
        ],
    }


@app.get("/health", summary="Basic health check")
def health_check():
    return {"status": "UP", "service": "AEROS"}
