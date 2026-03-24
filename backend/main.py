"""
Coupon Management — FastAPI Application

Serves the React frontend as static files and exposes API endpoints
that query the Databricks SQL Warehouse for coupon/offer data.

Key differences from the twins project:
  - Uses databricks-sql-connector (synchronous) instead of asyncpg
  - No Lakebase; targets a SQL Warehouse directly
  - Sync endpoints throughout (no async def required for route handlers)
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.db import close_connection, init_caches
from backend.routes import meta, offers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — cache warm on startup, cleanup on shutdown."""
    logger.info("Starting Coupon Management application...")
    try:
        init_caches()
        logger.info("Application ready")
    except Exception as exc:
        logger.warning("Cache warm-up failed (%s) — caches will load on first request", exc)
    yield
    logger.info("Shutting down...")
    close_connection()


app = FastAPI(
    title="Coupon Management",
    description="Domino's coupon/offer management tool powered by Databricks SQL Warehouse",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins in dev/demo mode
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
app.include_router(offers.router)
app.include_router(meta.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint for Databricks Apps readiness probe."""
    return {"status": "ok", "app": "coupons"}


# ---------------------------------------------------------------------------
# Serve React SPA (if frontend has been built)
# ---------------------------------------------------------------------------
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"

if (FRONTEND_DIR / "index.html").exists():
    # Serve static assets (JS, CSS, images) under /assets
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    # SPA catch-all: serve index.html for all non-API routes so React Router works
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        index = FRONTEND_DIR / "index.html"
        return FileResponse(str(index))

    logger.info("Serving frontend from %s", FRONTEND_DIR)
else:
    logger.warning(
        "Frontend dist directory not found at %s — API-only mode", FRONTEND_DIR
    )
