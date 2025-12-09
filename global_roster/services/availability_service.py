"""Availability service for computing trader availability from patterns, requests, and preferences."""
from datetime import date, timedelta
from typing import Dict, List, Literal, Tuple

from pydantic import BaseModel
from sqlalchemy.orm import Session

from global_roster.models.preferences import TraderPreference
from global_roster.models.trader import Trader
from global_roster.models.trader_request import TraderRequest, TraderRequestEffectType, TraderRequestStatus
from global_roster.models.weekly_pattern import TraderWeeklyPattern
from global_roster.services import trader_request_service

# Type aliases
AvailabilityStatus = Literal["MANDATORY", "UNAVAILABLE", "AVAILABLE"]
ShiftType = str  # "FULL", "EARLY", "MID", "LATE", etc.

# Standard shift types to consider
STANDARD_SHIFT_TYPES: List[ShiftType] = ["FULL", "EARLY", "MID", "LATE"]


class AvailabilityCell(BaseModel):
    """Represents availability for a single (date, shift_type) cell."""
    status: AvailabilityStatus
    weight: int  # -1, 0, +1 for AVAILABLE; 0 for MANDATORY/UNAVAILABLE
    # Reserved for future: reason: Optional[str] = None


def get_week_dates(week_start: date) -> List[date]:
    """Return a 7-element list from week_start (inclusive) to week_start+6.
    
    Args:
        week_start: The Monday of the week (or any day, will be normalized to Monday)
        
    Returns:
        List of 7 dates starting from Monday of the week containing week_start
    """
    # Find Monday of the week containing week_start
    days_since_monday = week_start.weekday()  # 0=Monday, 6=Sunday
    monday = week_start - timedelta(days=days_since_monday)
    
    return [monday + timedelta(days=i) for i in range(7)]


def _get_day_of_week(d: date) -> int:
    """Get day of week as integer (0=Monday, 6=Sunday)."""
    return d.weekday()


def _date_range_inclusive(start: date, end: date) -> List[date]:
    """Generate all dates in [start, end] inclusive."""
    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def _get_weekly_pattern_map(
    db: Session,
    trader_id: int,
) -> Dict[Tuple[int, str], TraderWeeklyPattern]:
    """Get weekly pattern as a map from (day_of_week, shift_type) to pattern row.
    
    Returns:
        Dict mapping (day_of_week, shift_type) to TraderWeeklyPattern
    """
    patterns = (
        db.query(TraderWeeklyPattern)
        .filter(TraderWeeklyPattern.trader_id == trader_id)
        .all()
    )
    return {(p.day_of_week, p.shift_type): p for p in patterns}


def _get_days_off_grouping_preference(
    db: Session,
    trader_id: int,
) -> int:
    """Get the days-off grouping preference weight for a trader.
    
    Returns:
        Weight value: +2 (prefers back-to-back), -2 (prefers split), 0 (no preference)
    """
    pref = (
        db.query(TraderPreference)
        .filter(
            TraderPreference.trader_id == trader_id,
            TraderPreference.category == "DAYS_OFF_GROUPING",
            TraderPreference.key == "PREFERENCE",
        )
        .first()
    )
    return pref.weight if pref else 0


def _apply_request_to_cells(
    request: TraderRequest,
    week_dates: List[date],
    shift_types: List[str],
    cells: Dict[Tuple[date, str], AvailabilityCell],
) -> None:
    """Apply a single request to the availability cells.
    
    Modifies cells in-place.
    
    Args:
        request: The TraderRequest to apply
        week_dates: List of 7 dates in the week
        shift_types: List of shift types to consider
        cells: Dict mapping (date, shift_type) to AvailabilityCell (modified in-place)
    """
    # Get all dates covered by this request
    request_dates = _date_range_inclusive(request.date_from, request.date_to)
    
    # Filter to only dates in this week
    week_dates_set = set(week_dates)
    applicable_dates = [d for d in request_dates if d in week_dates_set]
    
    if not applicable_dates:
        return  # Request doesn't overlap with this week
    
    # Determine which shifts this applies to
    if request.shift_type is None:
        # Applies to all shifts on these dates
        applicable_shifts = shift_types
    else:
        # Applies only to the specific shift
        applicable_shifts = [request.shift_type] if request.shift_type in shift_types else []
    
    # Apply the effect
    for d in applicable_dates:
        for shift in applicable_shifts:
            key = (d, shift)
            if key in cells:
                # Precedence: MANDATORY > UNAVAILABLE
                if request.effect_type == TraderRequestEffectType.MANDATORY:
                    cells[key] = AvailabilityCell(status="MANDATORY", weight=0)
                elif request.effect_type == TraderRequestEffectType.UNAVAILABLE:
                    # Only set UNAVAILABLE if not already MANDATORY
                    if cells[key].status != "MANDATORY":
                        cells[key] = AvailabilityCell(status="UNAVAILABLE", weight=0)


def compute_trader_week_availability(
    db: Session,
    trader_id: int,
    week_start: date,
    shift_types: List[str] | None = None,
) -> Dict[Tuple[date, str], AvailabilityCell]:
    """
    For a single trader, return availability for 7 days × all shift_types.
    
    Precedence rules (applied in order):
    1. APPROVED MANDATORY request → status = "MANDATORY"
    2. APPROVED UNAVAILABLE request → status = "UNAVAILABLE"
    3. Weekly pattern hard_block = True → status = "UNAVAILABLE"
    4. Otherwise → status = "AVAILABLE", weight from weekly pattern
    
    Args:
        db: Database session
        trader_id: Trader ID
        week_start: Start date of the week (will be normalized to Monday)
        shift_types: Optional list of shift types to consider. Defaults to STANDARD_SHIFT_TYPES.
        
    Returns:
        Dict mapping (date, shift_type) to AvailabilityCell
    """
    if shift_types is None:
        shift_types = STANDARD_SHIFT_TYPES
    
    # Get week dates
    week_dates = get_week_dates(week_start)
    
    # Initialize all cells as AVAILABLE with default weight
    cells: Dict[Tuple[date, str], AvailabilityCell] = {}
    pattern_map = _get_weekly_pattern_map(db, trader_id)
    
    for d in week_dates:
        day_of_week = _get_day_of_week(d)
        for shift in shift_types:
            key = (d, shift)
            pattern = pattern_map.get((day_of_week, shift))
            
            if pattern and pattern.hard_block:
                # Hard block from weekly pattern
                cells[key] = AvailabilityCell(status="UNAVAILABLE", weight=0)
            else:
                # Default: AVAILABLE with weight from pattern
                weight = pattern.weight if pattern else 0
                cells[key] = AvailabilityCell(status="AVAILABLE", weight=weight)
    
    # Apply APPROVED requests (only APPROVED requests affect availability)
    approved_requests = trader_request_service.get_approved_requests_for_trader(
        db,
        trader_id,
        date_from=week_dates[0],
        date_to=week_dates[-1],
    )
    
    # Apply requests in order (MANDATORY requests should be applied first for clarity)
    # But since we check precedence in _apply_request_to_cells, order doesn't matter
    for req in approved_requests:
        _apply_request_to_cells(req, week_dates, shift_types, cells)
    
    return cells


def compute_all_traders_week_availability(
    db: Session,
    week_start: date,
    shift_types: List[str] | None = None,
) -> Dict[int, Dict[Tuple[date, str], AvailabilityCell]]:
    """
    For all ACTIVE traders, return a nested dict of availability.
    
    Args:
        db: Database session
        week_start: Start date of the week (will be normalized to Monday)
        shift_types: Optional list of shift types to consider. Defaults to STANDARD_SHIFT_TYPES.
        
    Returns:
        Nested dict: { trader_id: { (date, shift_type): AvailabilityCell, ... }, ... }
    """
    if shift_types is None:
        shift_types = STANDARD_SHIFT_TYPES
    
    # Get all active traders
    traders = db.query(Trader).filter(Trader.is_active == True).all()
    
    result: Dict[int, Dict[Tuple[date, str], AvailabilityCell]] = {}
    
    for trader in traders:
        result[trader.id] = compute_trader_week_availability(
            db,
            trader.id,
            week_start,
            shift_types,
        )
    
    return result


# Debug/test function
if __name__ == "__main__":
    """Simple debug function to test availability computation."""
    from global_roster.core.db import SessionLocal
    
    # Example: compute availability for trader 1 for current week
    db = SessionLocal()
    try:
        # Get Monday of current week
        today = date.today()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        
        trader_id = 1
        availability = compute_trader_week_availability(db, trader_id, monday)
        
        print(f"\nAvailability for trader {trader_id} (week starting {monday}):")
        print("=" * 80)
        
        week_dates = get_week_dates(monday)
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for shift in STANDARD_SHIFT_TYPES:
            print(f"\n{shift} shift:")
            for i, d in enumerate(week_dates):
                key = (d, shift)
                cell = availability.get(key)
                if cell:
                    status_symbol = {
                        "MANDATORY": "✓",
                        "UNAVAILABLE": "✗",
                        "AVAILABLE": "○",
                    }.get(cell.status, "?")
                    weight_str = f" (w:{cell.weight})" if cell.status == "AVAILABLE" else ""
                    print(f"  {day_names[i]} {d}: {status_symbol} {cell.status}{weight_str}")
        
    finally:
        db.close()



