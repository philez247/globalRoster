"""Traders router."""
from datetime import date as date_type
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from global_roster.core.config import TEMPLATES_DIR
from global_roster.core.db import get_db
from global_roster.models.trader import Trader
from global_roster.schemas.weekly_pattern import DaySportPreference
from global_roster.schemas.trader import TraderCreate, TraderRead, TraderUpdate
from global_roster.schemas.weekly_pattern import WeeklyPatternUpdateRequest
from global_roster.services import preferences_service, trader_service, weekly_pattern_service
from global_roster.services import config_service

router = APIRouter(prefix="/traders", tags=["Traders"])
api_router = APIRouter(prefix="/api/traders", tags=["Traders API"])

# Configure Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

DAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SHIFT_TYPES = ["FULL", "EARLY", "LATE"]  # Note: MID removed to match frontend modal


def _build_weekly_pattern_days(pattern_grid, days_off_preference):
    """Build the days structure for weekly pattern template."""
    days = []
    pattern_map = {(row.day_of_week, row.shift_type): row for row in pattern_grid}
    
    for day_idx, day_label in enumerate(DAY_LABELS):
        shifts = []
        for shift_type in SHIFT_TYPES:
            row = pattern_map.get((day_idx, shift_type))
            if row:
                if row.hard_block:
                    state = "absolute_no"
                elif row.weight == 1:
                    state = "preferred_shift"
                elif row.weight == -1:
                    state = "preferred_not_work"
                else:
                    state = "indifferent"
            else:
                state = "indifferent"
            
            shifts.append({
                "type": shift_type,
                "state": state,
            })
        
        days.append({
            "label": day_label,
            "index": day_idx,
            "shifts": shifts,
        })
    
    return days


@router.get("", response_class=HTMLResponse)
def list_traders(request: Request, db: Session = Depends(get_db)):
    """List all traders (read-only)."""
    traders = trader_service.get_all(db)
    sports = config_service.get_sports(db)
    return templates.TemplateResponse(
        "traders.html",
        {"request": request, "traders": traders, "sports": sports}
    )


@router.get("/new", response_class=HTMLResponse)
def new_trader_form(request: Request, db: Session = Depends(get_db)):
    """Show create trader form."""
    from global_roster.services import config_service
    
    locations = config_service.get_locations(db)
    sports = config_service.get_sports(db)
    
    return templates.TemplateResponse(
        "trader_form.html",
        {
            "request": request,
            "locations": locations,
            "sports": sports,
        },
    )


@router.post("", response_class=RedirectResponse, name="traders_create")
def create_trader(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    location: str = Form(...),
    manager: str | None = Form(None),
    level: str | None = Form(None),
    primary_sport: str | None = Form(None),
    secondary_sport: str | None = Form(None),
    required_days_per_week: str = Form("5"),
    hours_per_week: str | None = Form(None),
    start_date: str | None = Form(None),
    alias: str = Form(...),
    redirect_to: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Create a new trader from form data."""
    # Construct name from first/last
    first = first_name.strip()
    last = last_name.strip()
    if not first or not last:
        raise HTTPException(status_code=400, detail="First name and last name are required.")
    
    full_name = f"{last}, {first}"
    
    # Convert form data to appropriate types
    level_int = int(level) if level and level.strip() else None
    required_days = int(required_days_per_week) if required_days_per_week else 5
    hours_per_week_int = int(hours_per_week) if hours_per_week and hours_per_week.strip() else None
    start_date_parsed = None
    if start_date and start_date.strip():
        try:
            start_date_parsed = date_type.fromisoformat(start_date)
        except ValueError:
            start_date_parsed = None
    
    # Normalize empty strings to None
    location_clean = location.strip() if location else ""
    manager_clean = manager.strip() if manager and manager.strip() else None
    alias_clean = alias.strip() if alias else ""
    primary_sport_clean = primary_sport.strip() if primary_sport and primary_sport.strip() else None
    secondary_sport_clean = secondary_sport.strip() if secondary_sport and secondary_sport.strip() else None
    
    # Create TraderCreate schema
    trader_data = TraderCreate(
        name=full_name,
        location=location_clean,
        manager=manager_clean,
        level=level_int,
        primary_sport=primary_sport_clean,
        secondary_sport=secondary_sport_clean,
        required_days_per_week=required_days,
        hours_per_week=hours_per_week_int,
        start_date=start_date_parsed,
        alias=alias_clean,
    )
    
    trader_service.create(db, trader_data)
    
    # Use redirect_to if provided, otherwise default to traders list
    target_url = redirect_to if redirect_to else "/traders"
    
    return RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{trader_id}", response_model=TraderRead)
def get_trader(trader_id: int, db: Session = Depends(get_db)):
    """Get a trader by ID as JSON."""
    trader = trader_service.get(db, trader_id)
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    return trader


@api_router.put("/{trader_id}", response_model=TraderRead)
async def update_trader_json(
    trader_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update a trader by ID (JSON API)."""
    trader = trader_service.get(db, trader_id)
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    payload = await request.json()
    
    # Convert payload to TraderUpdate schema
    update_data = TraderUpdate(**payload)
    
    # Update trader
    updated_trader = trader_service.update(db, trader_id, update_data)
    if updated_trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    return updated_trader


@router.get("/{trader_id}/weekly-pattern", response_class=HTMLResponse)
def trader_weekly_pattern_page(
    trader_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Show weekly pattern page."""
    trader = trader_service.get(db, trader_id)
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    pattern_grid = weekly_pattern_service.get_or_init_pattern(db, trader_id)
    days_off_weight = preferences_service.get_days_off_preference(db, trader_id)
    
    if days_off_weight > 0:
        days_off_preference = "BACK_TO_BACK"
    elif days_off_weight < 0:
        days_off_preference = "SPLIT"
    else:
        days_off_preference = "NONE"
    
    days = _build_weekly_pattern_days(pattern_grid, days_off_preference)
    
    return templates.TemplateResponse(
        "trader_weekly_pattern.html",
        {
            "request": request,
            "trader": trader,
            "days": days,
            "days_off_preference": days_off_preference,
        },
    )


@router.get("/{trader_id}/weekly-pattern/inner", response_class=HTMLResponse)
def trader_weekly_pattern_inner(
    trader_id: int,
    request: Request,
    db: Session = Depends(get_db),
    mode: str = "edit",
):
    """Get inner HTML for weekly pattern modal."""
    trader = trader_service.get(db, trader_id)
    if not trader:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    pattern_grid = weekly_pattern_service.get_or_init_pattern(db, trader_id)
    days_off_weight = preferences_service.get_days_off_preference(db, trader_id)
    
    if days_off_weight > 0:
        days_off_preference = "BACK_TO_BACK"
    elif days_off_weight < 0:
        days_off_preference = "SPLIT"
    else:
        days_off_preference = "NONE"
    
    days = _build_weekly_pattern_days(pattern_grid, days_off_preference)
    
    return templates.TemplateResponse(
        "partials/_trader_weekly_pattern_inner.html",
        {
            "request": request,
            "trader": trader,
            "days": days,
            "days_off_preference": days_off_preference,
            "mode": mode,
        },
    )


@api_router.get("/{trader_id}/weekly-pattern")
def get_weekly_pattern_json(
    trader_id: int,
    db: Session = Depends(get_db),
):
    """Get weekly pattern data as JSON for modal."""
    try:
        trader = db.query(Trader).filter(Trader.id == trader_id).first()
        if trader is None:
            raise HTTPException(status_code=404, detail="Trader not found")

        rows = weekly_pattern_service.get_or_init_pattern(db, trader_id)
        
        # Convert to JSON format - filter to only include shifts used by frontend (FULL, EARLY, LATE)
        cells = []
        for row in rows:
            # Only include shifts that the frontend modal uses
            if row.shift_type in ["FULL", "EARLY", "LATE"]:
                cells.append({
                    "day_of_week": row.day_of_week,
                    "shift_type": row.shift_type,
                    "hard_block": row.hard_block,
                    "weight": row.weight,
                })

        # Get days-off preference
        days_off_weight = preferences_service.get_days_off_preference(db, trader_id)
        
        if days_off_weight > 0:
            days_off_preference = "BACK_TO_BACK"
        elif days_off_weight < 0:
            days_off_preference = "SPLIT"
        else:
            days_off_preference = "NONE"

        # Day-sport preferences
        day_sport_rows = preferences_service.get_day_sport_preferences(db, trader_id)
        day_sport_prefs = [
            {"day_of_week": row.day_of_week, "sport_code": row.sport_code}
            for row in day_sport_rows
        ]

        return JSONResponse({
            "trader_id": trader_id,
            "trader_name": trader.name,
            "cells": cells,
            "days_off_preference": days_off_preference,
            "day_sport_preferences": day_sport_prefs,
        })
    except Exception as e:
        import traceback
        print(f"Error in get_weekly_pattern_json: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.post("/{trader_id}/weekly-pattern")
async def save_weekly_pattern(
    trader_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Save weekly pattern for a trader (JSON API)."""
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")

    payload = await request.json()
    data = WeeklyPatternUpdateRequest(**payload)

    if data.trader_id != trader_id:
        raise HTTPException(status_code=400, detail="Trader ID mismatch")

    # Save grid
    weekly_pattern_service.save_pattern(db, trader_id, data.cells)

    # Map days_off_preference to weight and save
    if data.days_off_preference == "BACK_TO_BACK":
        weight = 2
    elif data.days_off_preference == "SPLIT":
        weight = -2
    else:
        weight = 0

    # Save days-off preference
    preferences_service.set_days_off_preference(db, trader_id, weight)

    # Save day-sport preferences (replace existing)
    preferences_service.set_day_sport_preferences(db, trader_id, data.day_sport_preferences or [])

    return JSONResponse({"status": "ok"})


@router.post("/{trader_id}/deactivate")
def deactivate_trader(trader_id: int, db: Session = Depends(get_db)):
    """Deactivate a trader by setting is_active = False."""
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if not trader:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    if not trader.is_active:
        # already inactive; nothing to do
        return {"ok": True, "status": "already_inactive"}
    
    trader.is_active = False
    db.commit()
    return {"ok": True, "status": "deactivated"}


@router.post("/{trader_id}/delete")
def delete_trader(trader_id: int, db: Session = Depends(get_db)):
    """Permanently delete a trader (only allowed if inactive)."""
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if not trader:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    if trader.is_active:
        raise HTTPException(
            status_code=400,
            detail="Trader must be inactive before permanent delete",
        )
    
    db.delete(trader)
    db.commit()
    return {"ok": True, "status": "deleted"}

