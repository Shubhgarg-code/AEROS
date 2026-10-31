"""AEROS FastAPI Web Service and Routing Package."""

from aeros.api.main import app
from aeros.api.routes import router

__all__ = ["app", "router"]
