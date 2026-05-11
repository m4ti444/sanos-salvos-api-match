"""
Sanos y Salvos — Match Engine
Core algorithm that identifies potential matches between lost and found pets.

Scoring Weights:
  - Breed:     30%
  - Color:     25%
  - Size:      15%
  - Proximity: 20%
  - Date:      10%
"""

import math
import logging
from datetime import datetime
from typing import List

from app.repositories.match_repository import MatchRepository
from app.factories.match_factory import MatchFactory

logger = logging.getLogger("match_engine")

# Minimum score threshold to consider a match
MATCH_THRESHOLD = 40.0


class MatchEngine:
    """
    Analyzes reports and identifies potential matches using
    a weighted scoring algorithm.
    """

    @staticmethod
    def _normalize_string(s: str) -> str:
        """Normalize strings for comparison."""
        if not s:
            return ""
        return s.strip().lower()

    @staticmethod
    def _score_breed(breed1: str, breed2: str) -> float:
        """Score breed similarity (0-100). Exact match = 100, partial = 50."""
        b1 = MatchEngine._normalize_string(breed1)
        b2 = MatchEngine._normalize_string(breed2)

        if not b1 or not b2:
            return 30  # Unknown breeds get a neutral score

        if b1 == b2:
            return 100

        # Partial match (one contains the other)
        if b1 in b2 or b2 in b1:
            return 70

        # Check for common words
        words1 = set(b1.split())
        words2 = set(b2.split())
        common = words1 & words2
        if common:
            return 50

        return 0

    @staticmethod
    def _score_color(color1: str, color2: str) -> float:
        """Score color similarity."""
        c1 = MatchEngine._normalize_string(color1)
        c2 = MatchEngine._normalize_string(color2)

        if not c1 or not c2:
            return 30

        if c1 == c2:
            return 100

        # Partial match
        if c1 in c2 or c2 in c1:
            return 75

        # Check common color words
        words1 = set(c1.replace(",", " ").split())
        words2 = set(c2.replace(",", " ").split())
        common = words1 & words2
        if common:
            return 60

        return 0

    @staticmethod
    def _score_size(size1: str, size2: str) -> float:
        """Score size match."""
        s1 = MatchEngine._normalize_string(size1)
        s2 = MatchEngine._normalize_string(size2)

        if not s1 or not s2:
            return 30

        if s1 == s2:
            return 100

        # Adjacent sizes get partial credit
        size_order = ["pequeño", "mediano", "grande"]
        try:
            idx1 = size_order.index(s1)
            idx2 = size_order.index(s2)
            diff = abs(idx1 - idx2)
            if diff == 1:
                return 50
        except ValueError:
            pass

        return 0

    @staticmethod
    def _score_proximity(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Score geographic proximity using Haversine formula."""
        if not all([lat1, lng1, lat2, lng2]):
            return 30

        # Haversine formula
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = R * c

        # Score based on distance
        if distance_km <= 1:
            return 100
        elif distance_km <= 3:
            return 80
        elif distance_km <= 5:
            return 60
        elif distance_km <= 10:
            return 40
        elif distance_km <= 20:
            return 20
        else:
            return 5

    @staticmethod
    def _score_date(date1_str: str, date2_str: str) -> float:
        """Score temporal proximity (closer dates = higher score)."""
        if not date1_str or not date2_str:
            return 30

        try:
            d1 = datetime.fromisoformat(str(date1_str))
            d2 = datetime.fromisoformat(str(date2_str))
            diff_days = abs((d2 - d1).days)

            if diff_days <= 1:
                return 100
            elif diff_days <= 3:
                return 80
            elif diff_days <= 7:
                return 60
            elif diff_days <= 14:
                return 40
            elif diff_days <= 30:
                return 20
            else:
                return 5
        except (ValueError, TypeError):
            return 30

    @classmethod
    def calculate_score(cls, report1: dict, report2: dict) -> tuple:
        """
        Calculate match score between two reports.
        Returns (total_score, score_breakdown).
        """
        # Species must match
        sp1 = cls._normalize_string(report1.get("species", ""))
        sp2 = cls._normalize_string(report2.get("species", ""))
        if sp1 and sp2 and sp1 != sp2:
            return 0.0, {"species_mismatch": True}

        breed_score = cls._score_breed(report1.get("breed", ""), report2.get("breed", ""))
        color_score = cls._score_color(report1.get("color", ""), report2.get("color", ""))
        size_score = cls._score_size(report1.get("size", ""), report2.get("size", ""))
        proximity_score = cls._score_proximity(
            report1.get("latitude", 0), report1.get("longitude", 0),
            report2.get("latitude", 0), report2.get("longitude", 0),
        )
        date_score = cls._score_date(report1.get("date_event"), report2.get("date_event"))

        # Weighted total
        total = (
            breed_score * 0.30
            + color_score * 0.25
            + size_score * 0.15
            + proximity_score * 0.20
            + date_score * 0.10
        )

        breakdown = {
            "breed": {"score": breed_score, "weight": 0.30, "weighted": breed_score * 0.30},
            "color": {"score": color_score, "weight": 0.25, "weighted": color_score * 0.25},
            "size": {"score": size_score, "weight": 0.15, "weighted": size_score * 0.15},
            "proximity": {"score": proximity_score, "weight": 0.20, "weighted": proximity_score * 0.20},
            "date": {"score": date_score, "weight": 0.10, "weighted": date_score * 0.10},
        }

        return total, breakdown

    @classmethod
    async def process_new_report(cls, report_data: dict) -> List[dict]:
        """
        Process a newly reported pet and find potential matches.
        - If report is 'perdido', compare against 'encontrado' reports.
        - If report is 'encontrado', compare against 'perdido' reports.
        """
        report_type = report_data.get("report_type")
        opposite_type = "encontrado" if report_type == "perdido" else "perdido"

        # Cache this report
        await MatchRepository.cache_report(report_data)

        # Get opposite type reports
        candidates = await MatchRepository.get_active_reports(opposite_type)

        matches_found = []

        for candidate in candidates:
            # Skip same species check
            score, breakdown = cls.calculate_score(report_data, candidate)

            if score >= MATCH_THRESHOLD:
                # Determine which is lost and which is found
                if report_type == "perdido":
                    lost_report = report_data
                    found_report = candidate
                else:
                    lost_report = candidate
                    found_report = report_data

                # Use Factory Method to create match
                match = MatchFactory.create_match(lost_report, found_report, score, breakdown)
                match_dict = match.model_dump()

                # Save to MongoDB
                match_id = await MatchRepository.save_match(match_dict)
                match_dict["_id"] = match_id

                matches_found.append(match_dict)
                logger.info(
                    f"🎯 Match found! Score: {score:.1f}% — "
                    f"Lost #{lost_report['report_id']} ↔ Found #{found_report['report_id']}"
                )

        return matches_found
