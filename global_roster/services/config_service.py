"""Configuration service for locations and sports."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from global_roster.models.config import LocationConfig, SportConfig


def get_locations(db: Session) -> list[LocationConfig]:
    """Get all active locations, ordered by code."""
    return (
        db.query(LocationConfig)
        .filter(LocationConfig.is_active.is_(True))
        .order_by(LocationConfig.code)
        .all()
    )


def create_location(db: Session, code: str, name: str | None = None) -> LocationConfig:
    """Create a new location. Raises error if location already exists."""
    code = code.strip().upper()
    # Use code as name if name not provided
    name = (name.strip() if name else code)
    
    # Check if location already exists
    existing = (
        db.query(LocationConfig)
        .filter(LocationConfig.code == code)
        .one_or_none()
    )
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=400, detail="Location already exists")
        # Reactivate if inactive
        existing.is_active = True
        existing.name = name
        db.commit()
        db.refresh(existing)
        return existing

    loc = LocationConfig(code=code, name=name, is_active=True)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def get_sports(db: Session) -> list[SportConfig]:
    """Get all active sports, ordered by code."""
    return (
        db.query(SportConfig)
        .filter(SportConfig.is_active.is_(True))
        .order_by(SportConfig.code)
        .all()
    )


def create_sport(db: Session, code: str, name: str) -> SportConfig:
    """Create a new sport or reactivate existing one."""
    code = code.strip().upper()
    name = name.strip()
    existing = (
        db.query(SportConfig)
        .filter(SportConfig.code == code)
        .one_or_none()
    )
    if existing:
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    sport = SportConfig(code=code, name=name, is_active=True)
    db.add(sport)
    db.commit()
    db.refresh(sport)
    return sport

