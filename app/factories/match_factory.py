"""
Sanos y Salvos — Match Factory Method Pattern
Creates match result instances with calculated scores.
"""

from datetime import datetime
from app.models.match import MatchResult


class MatchFactory:
    """
    Factory Method Pattern — creates MatchResult instances
    based on the comparison of two reports.
    """

    @staticmethod
    def create_match(
        report_lost: dict,
        report_found: dict,
        score: float,
        score_breakdown: dict,
    ) -> MatchResult:
        """Create a new MatchResult with all computed data."""
        return MatchResult(
            report_lost_id=report_lost["report_id"],
            report_found_id=report_found["report_id"],
            score=round(score, 2),
            score_breakdown=score_breakdown,
            status="pendiente",
            pet_lost_name=report_lost.get("pet_name"),
            pet_found_name=report_found.get("pet_name"),
            user_lost_id=report_lost.get("user_id", 0),
            user_found_id=report_found.get("user_id", 0),
            created_at=datetime.utcnow(),
            notified=False,
        )
