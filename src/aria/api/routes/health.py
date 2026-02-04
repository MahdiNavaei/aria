"""Health endpoints for ARIA API."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health() -> dict[str, str]:
    """Return basic health status."""
    return {"status": "ok"}
