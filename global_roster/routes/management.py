"""Management router."""
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from global_roster.core.config import TEMPLATES_DIR
from global_roster.core.db import get_db
from global_roster.models.trader import Trader
from global_roster.services import config_service, preferences_service
from global_roster.services.daily_resources_service import get_daily_resources_report
from global_roster.services.trader_request_service import get_all_requests_with_trader

router = APIRouter()

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/management", response_class=HTMLResponse)
def management_home(request: Request, db: Session = Depends(get_db)):
    """Management hub page."""
    locations = config_service.get_locations(db)
    sports = config_service.get_sports(db)
    requests_list = get_all_requests_with_trader(db)
    
    # Fetch active traders for Remove Trader modal
    active_traders = (
        db.query(Trader)
        .filter(Trader.is_active == True)  # noqa: E712
        .order_by(Trader.name)
        .all()
    )
    
    return templates.TemplateResponse(
        "management.html",
        {
            "request": request,
            "locations": locations,
            "sports": sports,
            "requests": requests_list,
            "active_traders": active_traders,
        },
    )


@router.get(
    "/management/daily-resources",
    response_class=HTMLResponse,
    name="daily_resources_page",
)
def daily_resources_page(
    request: Request,
    date: Optional[date_type] = Query(None),
    location: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Show the Daily Resources report for a given date and location."""
    selected_date = date or date_type.today()
    selected_location = location or None

    rows = get_daily_resources_report(db, selected_date, selected_location)
    locations = config_service.get_locations(db)

    return templates.TemplateResponse(
        "daily_resources.html",
        {
            "request": request,
            "selected_date": selected_date,
            "selected_location": selected_location,
            "locations": locations,
            "rows": rows,
        },
    )


@router.get("/management/preferences", response_class=HTMLResponse)
def management_preferences(
    request: Request,
    db: Session = Depends(get_db),
):
    """Management preferences table view."""
    prefs = preferences_service.get_days_off_preferences_summary(db)
    return templates.TemplateResponse(
        "management_preferences.html",
        {
            "request": request,
            "preferences": prefs,
        },
    )

