"""
Sanos y Salvos — Match Repository (PostgreSQL)
"""

from typing import List, Optional
import uuid
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.config import AsyncSessionLocal
from app.models.match import MatchDB, ReportCacheDB


class MatchRepository:
    """Repository for Match CRUD operations on PostgreSQL via SQLAlchemy."""

    @staticmethod
    async def save_match(match_data: dict) -> str:
        async with AsyncSessionLocal() as session:
            # Pydantic dict to SQLAlchemy model
            match_id = uuid.uuid4()
            db_match = MatchDB(
                id=match_id,
                report_lost_id=match_data.get("report_lost_id"),
                report_found_id=match_data.get("report_found_id"),
                score=match_data.get("score"),
                score_breakdown=match_data.get("score_breakdown"),
                status=match_data.get("status", "pendiente"),
                pet_lost_name=match_data.get("pet_lost_name"),
                pet_found_name=match_data.get("pet_found_name"),
                user_lost_id=match_data.get("user_lost_id"),
                user_found_id=match_data.get("user_found_id"),
                notified=match_data.get("notified", False)
            )
            session.add(db_match)
            await session.commit()
            return str(match_id)

    @staticmethod
    async def get_by_id(match_id: str) -> Optional[dict]:
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(MatchDB).where(MatchDB.id == uuid.UUID(match_id))
            except ValueError:
                return None
            result = await session.execute(stmt)
            match = result.scalar_one_or_none()
            if match:
                d = {c.name: getattr(match, c.name) for c in match.__table__.columns}
                d["_id"] = str(d.pop("id"))
                d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                return d
            return None

    @staticmethod
    async def get_all(skip: int = 0, limit: int = 50) -> List[dict]:
        async with AsyncSessionLocal() as session:
            stmt = select(MatchDB).order_by(desc(MatchDB.created_at)).offset(skip).limit(limit)
            result = await session.execute(stmt)
            matches = result.scalars().all()
            
            results = []
            for match in matches:
                d = {c.name: getattr(match, c.name) for c in match.__table__.columns}
                d["_id"] = str(d.pop("id"))
                d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                results.append(d)
            return results

    @staticmethod
    async def get_by_report(report_id: int) -> List[dict]:
        async with AsyncSessionLocal() as session:
            stmt = select(MatchDB).where(
                or_(
                    MatchDB.report_lost_id == report_id,
                    MatchDB.report_found_id == report_id
                )
            ).order_by(desc(MatchDB.score))
            result = await session.execute(stmt)
            matches = result.scalars().all()
            
            results = []
            for match in matches:
                d = {c.name: getattr(match, c.name) for c in match.__table__.columns}
                d["_id"] = str(d.pop("id"))
                d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                results.append(d)
            return results

    @staticmethod
    async def update_status(match_id: str, status: str) -> bool:
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(MatchDB).where(MatchDB.id == uuid.UUID(match_id))
            except ValueError:
                return False
            result = await session.execute(stmt)
            match = result.scalar_one_or_none()
            if match:
                match.status = status
                await session.commit()
                return True
            return False

    @staticmethod
    async def cache_report(report_data: dict):
        """Cache report data in PostgreSQL for matching."""
        async with AsyncSessionLocal() as session:
            stmt = select(ReportCacheDB).where(ReportCacheDB.report_id == report_data.get("report_id"))
            result = await session.execute(stmt)
            cache_entry = result.scalar_one_or_none()
            
            # Convert date_event string to date object if needed
            date_evt = report_data.get("date_event")
            if isinstance(date_evt, str):
                try:
                    date_evt = datetime.fromisoformat(date_evt.split('T')[0]).date()
                except ValueError:
                    date_evt = None
                    
            if cache_entry:
                cache_entry.report_type = report_data.get("report_type")
                cache_entry.pet_name = report_data.get("pet_name")
                cache_entry.species = report_data.get("species")
                cache_entry.breed = report_data.get("breed")
                cache_entry.color = report_data.get("color")
                cache_entry.size = report_data.get("size")
                cache_entry.latitude = report_data.get("latitude")
                cache_entry.longitude = report_data.get("longitude")
                cache_entry.date_event = date_evt
                cache_entry.user_id = report_data.get("user_id")
            else:
                cache_entry = ReportCacheDB(
                    report_id=report_data.get("report_id"),
                    report_type=report_data.get("report_type"),
                    pet_name=report_data.get("pet_name"),
                    species=report_data.get("species"),
                    breed=report_data.get("breed"),
                    color=report_data.get("color"),
                    size=report_data.get("size"),
                    latitude=report_data.get("latitude"),
                    longitude=report_data.get("longitude"),
                    date_event=date_evt,
                    user_id=report_data.get("user_id")
                )
                session.add(cache_entry)
            await session.commit()

    @staticmethod
    async def get_active_reports(report_type: str) -> List[dict]:
        """Get cached reports by type for matching."""
        async with AsyncSessionLocal() as session:
            stmt = select(ReportCacheDB).where(ReportCacheDB.report_type == report_type)
            result = await session.execute(stmt)
            reports = result.scalars().all()
            
            results = []
            for r in reports:
                # Convert back to dict expected by match engine
                d = {c.name: getattr(r, c.name) for c in r.__table__.columns}
                if d.get("date_event"):
                    d["date_event"] = d["date_event"].isoformat()
                if d.get("created_at"):
                    d["created_at"] = d["created_at"].isoformat()
                results.append(d)
            return results
