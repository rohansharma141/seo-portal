"""FastAPI application entry point — Building10X SEO Portal.

Run locally with:  uvicorn main:app --reload   (from the backend/ directory)

Step 1 scaffolding covers: the app, CORS (Section 14), the lifespan hook, and
the public /health endpoint (Section 7.1). Router wiring (Section 7, Step 6)
and the APScheduler startup (Section 9, Step 7) have explicit TODO markers
below so later steps have an unambiguous insertion point.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("seo_portal")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting %s v%s (environment=%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    if settings.scheduler_enabled:
        from services.scheduler import setup_scheduler

        setup_scheduler(app)
    else:
        logger.info("Scheduler disabled (scheduler_enabled=False)")
    yield
    if settings.scheduler_enabled:
        from services.scheduler import shutdown_scheduler

        shutdown_scheduler()
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Standalone SEO auditing portal + REST API. "
        "See docs/SEO_PORTAL_BUILD_DOC.md for the full contract."
    ),
    lifespan=lifespan,
)

# CORS — Section 14: allow only FRONTEND_URL in production. In development we
# allow the local Next.js dev origins. We never combine allow_origins=["*"]
# with allow_credentials=True (the browser rejects that combination), so an
# explicit origin list is used in every environment.
if settings.is_production:
    _allowed_origins = [settings.frontend_url]
else:
    _allowed_origins = sorted(
        {
            settings.frontend_url,
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Liveness probe. No authentication required (Section 7.1)."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# API routers (Section 7), mounted under /api/v1.
from routers import audits, reports, sites, tokens, webhooks  # noqa: E402

for _router in (
    sites.router,
    audits.router,
    reports.router,
    tokens.router,
    webhooks.router,
):
    app.include_router(_router, prefix="/api/v1")
