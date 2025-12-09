"""Trader service layer for business logic."""
import re
from sqlalchemy.orm import Session

from global_roster.models.trader import Trader
from global_roster.models.trader_sport_skill import TraderSportSkill
from global_roster.schemas.trader import TraderCreate, TraderUpdate


def _generate_alias(name: str) -> str:
    """Generate an alias from a name.
    
    Converts to lowercase and replaces spaces with underscores.
    Example: "John Smith" -> "john_smith"
    """
    alias = name.lower().strip()
    alias = re.sub(r'\s+', '_', alias)
    return alias


def _ensure_unique_alias(db: Session, base_alias: str) -> str | None:
    """Ensure alias is unique by appending suffix if needed.
    
    If alias exists, appends _2, _3, etc. until a free one is found.
    Returns None if base_alias is empty/None.
    """
    if not base_alias or not base_alias.strip():
        return None
    
    alias = base_alias.strip()
    counter = 1
    
    while db.query(Trader).filter(Trader.alias == alias).first() is not None:
        counter += 1
        alias = f"{base_alias.strip()}_{counter}"
    
    return alias


def get_all(db: Session) -> list[Trader]:
    """Get all active traders."""
    return db.query(Trader).filter(Trader.is_active == True).all()  # noqa: E712


def get(db: Session, trader_id: int) -> Trader | None:
    """Get a trader by ID."""
    return db.query(Trader).filter(Trader.id == trader_id).first()


def create(db: Session, data: TraderCreate) -> Trader:
    """Create a new trader.
    
    Alias is required and must be unique.
    """
    from fastapi import HTTPException
    
    # Enforce alias uniqueness at service level
    alias_clean = data.alias.strip() if data.alias else ""
    if not alias_clean:
        raise HTTPException(status_code=400, detail="Alias is required.")
    
    existing = (
        db.query(Trader)
        .filter(Trader.alias == alias_clean)
        .one_or_none()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Alias already exists.")
    
    # Create trader
    trader = Trader(
        name=data.name,
        location=data.location,
        alias=alias_clean,
        manager=data.manager,
        level=data.level,
        primary_sport=data.primary_sport,
        secondary_sport=data.secondary_sport,
        required_days_per_week=data.required_days_per_week,
        hours_per_week=data.hours_per_week,
        start_date=data.start_date,
        is_active=data.is_active,
    )
    
    db.add(trader)
    db.commit()
    db.refresh(trader)
    return trader


def update(db: Session, trader_id: int, data: TraderUpdate) -> Trader | None:
    """Update a trader by ID.
    
    Only updates fields that are provided (not None).
    """
    trader = get(db, trader_id)
    if trader is None:
        return None
    
    # Update each field only if value is not None
    if data.name is not None:
        trader.name = data.name
    if data.location is not None:
        trader.location = data.location
    if data.alias is not None:
        base_alias = data.alias.strip() if data.alias.strip() else None
        if base_alias:
            # Only check uniqueness if alias is different from current
            if base_alias != trader.alias:
                unique_alias = _ensure_unique_alias(db, base_alias)
                trader.alias = unique_alias
        else:
            trader.alias = None
    if data.manager is not None:
        trader.manager = data.manager
    if data.level is not None:
        trader.level = data.level
    if data.primary_sport is not None:
        trader.primary_sport = data.primary_sport
    if data.secondary_sport is not None:
        trader.secondary_sport = data.secondary_sport
    if data.required_days_per_week is not None:
        trader.required_days_per_week = data.required_days_per_week
    if data.hours_per_week is not None:
        trader.hours_per_week = data.hours_per_week
    if data.start_date is not None:
        trader.start_date = data.start_date
    if data.is_active is not None:
        trader.is_active = data.is_active
    
    # Sync sport skills if provided
    if data.skills is not None:
        # Delete all existing skills for this trader
        existing_skills = (
            db.query(TraderSportSkill)
            .filter(TraderSportSkill.trader_id == trader.id)
            .all()
        )
        for skill in existing_skills:
            db.delete(skill)

        # Add new skills from the skills array
        for skill_input in data.skills:
            if not skill_input.sport or not skill_input.level:
                continue
            try:
                level_int = int(skill_input.level)
                if level_int < 1 or level_int > 3:
                    continue
            except (ValueError, TypeError):
                continue

            new_skill = TraderSportSkill(
                trader_id=trader.id,
                sport_code=skill_input.sport,
                sport_level=level_int,
            )
            db.add(new_skill)

    db.commit()
    db.refresh(trader)
    return trader


def soft_delete(db: Session, trader_id: int) -> Trader | None:
    """Soft delete a trader by setting is_active to False."""
    trader = get(db, trader_id)
    if trader is None:
        return None
    
    trader.is_active = False
    db.commit()
    db.refresh(trader)
    return trader

