"""
Sanos y Salvos — Match API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.repositories.match_repository import MatchRepository

router = APIRouter(prefix="/api/matches", tags=["Coincidencias"])


class StatusUpdate(BaseModel):
    status: str  # confirmado, descartado


@router.get("/")
async def list_matches(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    """List all match results."""
    return await MatchRepository.get_all(skip, limit)


@router.get("/{match_id}")
async def get_match(match_id: str):
    """Get a specific match by ID."""
    match = await MatchRepository.get_by_id(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Coincidencia no encontrada")
    return match


@router.get("/report/{report_id}")
async def get_matches_for_report(report_id: int):
    """Get all matches for a specific report."""
    return await MatchRepository.get_by_report(report_id)


@router.patch("/{match_id}/status")
async def update_match_status(match_id: str, data: StatusUpdate):
    """Update match status (confirm or discard)."""
    success = await MatchRepository.update_status(match_id, data.status)
    if not success:
        raise HTTPException(status_code=404, detail="Coincidencia no encontrada")
    return {"message": "Estado actualizado", "status": data.status}
