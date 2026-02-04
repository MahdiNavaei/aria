"""ARIA FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aria.api.routes import analytics, health, jobs, metrics, profiles, tasks
from aria.api.websocket.server import app as ws_app
from aria.config import get_settings

settings = get_settings().api

app = FastAPI(
    title="ARIA API",
    description="Adaptive Reasoning & Intelligent Automation API",
    version="1.0.0",
)

if settings.cors.enabled:
    origins = settings.cors.origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(profiles.router, prefix="/api/profiles", tags=["Profiles"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

app.mount("/ws", ws_app)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"name": "ARIA API", "version": "1.0.0"}
