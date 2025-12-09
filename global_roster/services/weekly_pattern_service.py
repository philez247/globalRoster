"""Weekly pattern service."""
from typing import Iterable

from sqlalchemy.orm import Session

from global_roster.models.weekly_pattern import TraderWeeklyPattern
from global_roster.schemas.weekly_pattern import WeeklyPatternCell

SHIFT_TYPES: list[str] = ["FULL", "EARLY", "LATE"]  # Note: MID removed to match frontend
DAY_RANGE = range(0, 7)  # 0=Mon .. 6=Sun


def get_or_init_pattern(db: Session, trader_id: int) -> list:
    """
    Return full 7x4 grid for this trader.
    Create neutral defaults if missing (hard_block=False, weight=0).
    """
    existing = (
        db.query(TraderWeeklyPattern)
        .filter(TraderWeeklyPattern.trader_id == trader_id)
        .all()
    )
    existing_map = {(row.day_of_week, row.shift_type): row for row in existing}

    changed = False
    for day in DAY_RANGE:
        for shift in SHIFT_TYPES:
            key = (day, shift)
            if key not in existing_map:
                row = TraderWeeklyPattern(
                    trader_id=trader_id,
                    day_of_week=day,
                    shift_type=shift,
                    hard_block=False,
                    weight=0,
                )
                db.add(row)
                existing_map[key] = row
                changed = True

    if changed:
        db.commit()
        existing = (
            db.query(TraderWeeklyPattern)
            .filter(TraderWeeklyPattern.trader_id == trader_id)
            .order_by(TraderWeeklyPattern.day_of_week, TraderWeeklyPattern.shift_type)
            .all()
        )
    else:
        existing = sorted(
            existing_map.values(),
            key=lambda r: (r.day_of_week, r.shift_type),
        )

    return existing


def save_pattern(
    db: Session,
    trader_id: int,
    cells: Iterable[WeeklyPatternCell],
) -> None:
    """Save the weekly pattern cells for a trader."""
    rows = (
        db.query(TraderWeeklyPattern)
        .filter(TraderWeeklyPattern.trader_id == trader_id)
        .all()
    )
    row_map = {(r.day_of_week, r.shift_type): r for r in rows}

    for cell in cells:
        key = (cell.day_of_week, cell.shift_type)
        row = row_map.get(key)
        if row is None:
            row = TraderWeeklyPattern(
                trader_id=trader_id,
                day_of_week=cell.day_of_week,
                shift_type=cell.shift_type,
            )
            db.add(row)
            row_map[key] = row

        row.hard_block = cell.hard_block
        row.weight = cell.weight

    db.commit()

