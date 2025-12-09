"""Trader preferences service."""
from typing import List

from sqlalchemy.orm import Session

from global_roster.models.preferences import TraderPreference, TraderDaySportPreference
from global_roster.models.trader import Trader


def get_days_off_preference(db: Session, trader_id: int) -> int:
    """
    Returns the stored weight for DAYS_OFF_GROUPING (0, +2, -2),
    or 0 if not set.
    """
    pref = (
        db.query(TraderPreference)
        .filter(
            TraderPreference.trader_id == trader_id,
            TraderPreference.category == "DAYS_OFF_GROUPING",
            TraderPreference.key == "PREFERENCE",
        )
        .one_or_none()
    )
    return pref.weight if pref is not None else 0


def set_days_off_preference(db: Session, trader_id: int, weight: int) -> None:
    """
    Upserts the DAYS_OFF_GROUPING preference row.
    """
    pref = (
        db.query(TraderPreference)
        .filter(
            TraderPreference.trader_id == trader_id,
            TraderPreference.category == "DAYS_OFF_GROUPING",
            TraderPreference.key == "PREFERENCE",
        )
        .one_or_none()
    )

    if pref is None:
        pref = TraderPreference(
            trader_id=trader_id,
            category="DAYS_OFF_GROUPING",
            key="PREFERENCE",
            weight=weight,
        )
        db.add(pref)
    else:
        pref.weight = weight

    db.commit()


def get_day_sport_preferences(db: Session, trader_id: int) -> list[TraderDaySportPreference]:
    """Return all day-sport preferences for a trader."""
    return (
        db.query(TraderDaySportPreference)
        .filter(TraderDaySportPreference.trader_id == trader_id)
        .all()
    )


def set_day_sport_preferences(db: Session, trader_id: int, prefs: list) -> None:
    """Replace day-sport preferences for a trader."""
    # Clear existing rows
    db.query(TraderDaySportPreference).filter(
        TraderDaySportPreference.trader_id == trader_id
    ).delete()

    for pref in prefs:
        # Expect objects with day_of_week and sport_code
        if getattr(pref, "sport_code", None):
            db.add(
                TraderDaySportPreference(
                    trader_id=trader_id,
                    day_of_week=pref.day_of_week,
                    sport_code=pref.sport_code,
                )
            )

    db.commit()


def get_days_off_preferences_summary(db: Session) -> list[dict]:
    """
    Returns a list of dicts summarizing each active trader's days-off grouping preference.

    Each dict should have:
      - id
      - name
      - location
      - days_off_weight (int)
      - days_off_label (str)
    """
    traders = (
        db.query(Trader)
        .filter(Trader.is_active == True)
        .order_by(Trader.location, Trader.name)
        .all()
    )

    # Load all DAYS_OFF_GROUPING preferences in one go
    prefs = (
        db.query(TraderPreference)
        .filter(
            TraderPreference.category == "DAYS_OFF_GROUPING",
            TraderPreference.key == "PREFERENCE",
        )
        .all()
    )
    pref_map = {p.trader_id: p.weight for p in prefs}

    def label_for_weight(weight: int) -> str:
        if weight > 0:
            return "Back-to-back"
        elif weight < 0:
            return "Split"
        else:
            return "No preference"

    summary: list[dict] = []
    for t in traders:
        weight = pref_map.get(t.id, 0)
        summary.append(
            {
                "id": t.id,
                "name": t.name,
                "location": t.location,
                "days_off_weight": weight,
                "days_off_label": label_for_weight(weight),
            }
        )

    return summary

