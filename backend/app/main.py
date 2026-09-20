import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="StatStock", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["Content-Disposition"])

from .api.routes_health import router as health_router
from .api.routes_stocks import router as stocks_router
from .api.routes_analysis import router as analysis_router
from .api.routes_reports import router as reports_router

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(stocks_router, prefix="/api", tags=["stocks"])
app.include_router(analysis_router, prefix="/api", tags=["analysis"])
app.include_router(reports_router, prefix="/api", tags=["reports"])


try:
    Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)
except Exception:
    pass


def _frontend_dir() -> Path | None:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "frontend",   # backend/frontend layout: <root>/frontend
        here.parents[1] / "frontend",   # fallback if layout ever changes
        Path.cwd() / "frontend",
        Path.cwd().parent / "frontend",
    ]
    for c in candidates:
        if c.exists() and (c / "index.html").exists():
            return c
    return None


_frontend = _frontend_dir()
if _frontend is not None:
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")

    @app.get("/analysis.html", include_in_schema=False)
    def _analysis_page():
        f = _frontend / "analysis.html"
        if f.exists():
            return FileResponse(str(f))
        return FileResponse(str(_frontend / "index.html"))
else:
    logging.warning("Frontend directory not found; serving API only.")

    @app.get("/", include_in_schema=False)
    def _root():
        return {"service": "statstock", "docs": "/docs", "health": "/api/health"}
