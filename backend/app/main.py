import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .api.routes_health import router as health_router
from .api.routes_stocks import router as stocks_router
from .api.routes_analysis import router as analysis_router
from .api.routes_reports import router as reports_router

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="StatStock", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
                     expose_headers=["Content-Disposition"])

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(stocks_router, prefix="/api", tags=["stocks"])
app.include_router(analysis_router, prefix="/api", tags=["analysis"])
app.include_router(reports_router, prefix="/api", tags=["reports"])


_frontend = Path(__file__).resolve().parents[2] / "frontend"
if _frontend.exists():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
