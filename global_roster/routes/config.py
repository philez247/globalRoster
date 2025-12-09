"""Configuration router for locations and sports."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from global_roster.core.db import get_db
from global_roster.schemas.config import LocationCreate, LocationRead
from global_roster.services import config_service

router = APIRouter(prefix="/config", tags=["config"])


@router.post("/locations", response_model=LocationRead)
def add_location(payload: LocationCreate, db: Session = Depends(get_db)):
    """Add a new location."""
    try:
        loc = config_service.create_location(db, code=payload.code)
        return LocationRead(id=loc.id, code=loc.code)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sports")
def get_sports(db: Session = Depends(get_db)):
    """Get all active sports."""
    sports = config_service.get_sports(db)
    return [{"id": s.id, "code": s.code, "name": s.name} for s in sports]


@router.post("/sports")
def add_sport(code: str, name: str, db: Session = Depends(get_db)):
    """Add a new sport."""
    if not code.strip() or not name.strip():
        raise HTTPException(status_code=400, detail="Code and name are required.")
    sport = config_service.create_sport(db, code=code, name=name)
    return {"id": sport.id, "code": sport.code, "name": sport.name}

