"""Daily resources reporting service."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from global_roster.models.trader import Trader
from global_roster.models.trader_request import (
    TraderRequest,
    TraderRequestEffectType,
    TraderRequestStatus,
)
from global_roster.models.weekly_pattern import TraderWeeklyPattern


@dataclass
class DailyResourceRow:
    """Represents a trader's availability status for a single day."""

    id: int
    name: str
    alias: Optional[str]
    location: str
    status: str
    reason: str


def _classify_from_requests(requests: List[TraderRequest]) -> Optional[tuple[str, str]]:
    """Classify status based on approved requests covering the date."""
    if not requests:
        return None

    # UNAVAILABLE has highest priority, then MANDATORY
    for req in requests:
        effect = str(req.effect_type)
        if effect == TraderRequestEffectType.UNAVAILABLE.value:
            return "Absolute No", "Approved UNAVAILABLE request"
    for req in requests:
        effect = str(req.effect_type)
        if effect == TraderRequestEffectType.MANDATORY.value:
            return "Mandatory", "Approved MANDATORY request"

    return None


def _classify_from_pattern(pattern: TraderWeeklyPattern | None) -> tuple[str, str]:
    """Classify status using weekly pattern row."""
    if pattern is None:
        return "Neutral", "No specific preference"

    if pattern.hard_block:
        return "Absolute No", "Weekly pattern: Hard block"

    if pattern.weight > 0:
        return "Preferred In", "Weekly pattern: Preferred In"
    if pattern.weight < 0:
        return "Preferred Off", "Weekly pattern: Preferred Off"

    return "Neutral", "No specific preference"


def get_daily_resources_report(
    db: Session, target_date: date, location: Optional[str] = None
) -> list[DailyResourceRow]:
    """Compute per-trader availability for a specific date."""
    trader_query = db.query(Trader).filter(Trader.is_active.is_(True))
    if location:
        trader_query = trader_query.filter(Trader.location == location)

    traders = trader_query.all()
    trader_ids = [t.id for t in traders]
    if not trader_ids:
        return []

    # Approved requests covering the target date
    approved_requests = (
        db.query(TraderRequest)
        .filter(
            TraderRequest.trader_id.in_(trader_ids),
            TraderRequest.status == TraderRequestStatus.APPROVED.value,
            TraderRequest.date_from <= target_date,
            TraderRequest.date_to >= target_date,
        )
        .all()
    )
    requests_by_trader: Dict[int, List[TraderRequest]] = defaultdict(list)
    for req in approved_requests:
        requests_by_trader[req.trader_id].append(req)

    # Weekly pattern rows for the day (FULL shift only for this view)
    weekday = target_date.weekday()
    patterns = (
        db.query(TraderWeeklyPattern)
        .filter(
            TraderWeeklyPattern.trader_id.in_(trader_ids),
            TraderWeeklyPattern.day_of_week == weekday,
            TraderWeeklyPattern.shift_type == "FULL",
        )
        .all()
    )
    pattern_by_trader = {p.trader_id: p for p in patterns}

    rows: list[DailyResourceRow] = []
    for trader in traders:
        status = "Neutral"
        reason = "No specific preference"

        request_result = _classify_from_requests(requests_by_trader.get(trader.id, []))
        if request_result:
            status, reason = request_result
        else:
            pattern = pattern_by_trader.get(trader.id)
            status, reason = _classify_from_pattern(pattern)

        rows.append(
            DailyResourceRow(
                id=trader.id,
                name=trader.name,
                alias=trader.alias,
                location=trader.location,
                status=status,
                reason=reason,
            )
        )

    status_priority = {
        "Mandatory": 0,
        "Absolute No": 1,
        "Preferred In": 2,
        "Preferred Off": 3,
        "Neutral": 4,
    }

    rows.sort(
        key=lambda r: (
            r.location or "",
            status_priority.get(r.status, 99),
            r.name,
        )
    )

    return rows

