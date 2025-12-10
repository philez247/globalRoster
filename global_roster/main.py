"""Main FastAPI application."""
from datetime import date

from fastapi import Depends, FastAPI, Form, Query, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from global_roster.core.config import TEMPLATES_DIR, STATIC_DIR
from global_roster.core.db import get_db
from global_roster.core.security import (
    SESSION_COOKIE_NAME,
    SESSION_DURATION_HOURS,
    add_session,
    check_credentials,
    create_session,
    get_session_from_request,
    verify_session,
)
from global_roster.models.trader import Trader
from global_roster.models.config import LocationConfig, SportConfig
from global_roster.models.trader_request import TraderRequest
from global_roster.models.trader_sport_skill import TraderSportSkill
from global_roster.models.weekly_pattern import TraderWeeklyPattern
from global_roster.models.preferences import TraderPreference

app = FastAPI(title="Global Roster")


@app.on_event("startup")
async def startup_event():
    """Ensure Session table exists on startup."""
    from global_roster.models.base import Base
    from global_roster.models.session import Session as SessionModel
    from global_roster.core.db import engine
    
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)


# Mount static files FIRST (before middleware)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to check authentication for protected routes."""
    
    # Routes that don't require authentication
    PUBLIC_ROUTES = ["/login", "/static", "/docs", "/openapi.json", "/redoc", "/logout"]
    
    async def dispatch(self, request: Request, call_next):
        # Check if route is public
        path = request.url.path
        is_public = any(path.startswith(route) for route in self.PUBLIC_ROUTES)
        
        if not is_public:
            # Get database session
            db = next(get_db())
            try:
                # Check authentication
                session_token = get_session_from_request(request)
                if not session_token or not verify_session(session_token, db):
                    # Check if API request
                    accept_header = request.headers.get("accept", "")
                    if "application/json" in accept_header or "/api/" in path:
                        return HTMLResponse(
                            content='{"detail":"Unauthorized"}',
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            media_type="application/json",
                        )
                    # Redirect to login for HTML requests
                    return RedirectResponse(url="/login", status_code=307)
            finally:
                db.close()
        
        response = await call_next(request)
        return response


app.add_middleware(AuthMiddleware)

# Configure Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Handle login and set session cookie."""
    if not check_credentials(username, password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=401,
        )
    
    # Create session
    session_token = create_session()
    add_session(session_token, db)
    
    # Create response with redirect
    response = RedirectResponse(url="/", status_code=303)
    
    # Set cookie with 12-hour expiration
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_DURATION_HOURS * 3600,  # 12 hours in seconds
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
    )
    
    return response


@app.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    """Handle logout and clear session cookie."""
    from global_roster.core.security import get_session_from_request, remove_session
    
    session_token = get_session_from_request(request)
    if session_token:
        remove_session(session_token, db)
    
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response


@app.get("/", response_class=HTMLResponse)
def read_home(request: Request):
    """Home page route."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/traders", response_class=HTMLResponse)
def traders_page(
    request: Request,
    search: str = Query("", alias="search"),
    location: str = Query("", alias="location"),
    db: Session = Depends(get_db),
):
    """Traders page route with filtering."""
    from sqlalchemy import or_, func
    
    # Base query: active traders only
    query = db.query(Trader).filter(Trader.is_active == True)
    
    # Search filter: partial match on alias or name
    search_value = (search or "").strip()
    if search_value:
        pattern = f"%{search_value.lower()}%"
        query = query.filter(
            or_(
                func.lower(Trader.alias).like(pattern),
                func.lower(Trader.name).like(pattern),
            )
        )
    
    # Location filter: exact match
    location_value = (location or "").strip()
    if location_value:
        query = query.filter(Trader.location == location_value)
    
    # Order the final list
    traders = (
        query
        .order_by(Trader.name)
        .all()
    )
    
    # Distinct locations for dropdown
    loc_rows = (
        db.query(Trader.location)
        .filter(Trader.is_active == True)
        .distinct()
        .order_by(Trader.location)
        .all()
    )
    locations = [row[0] for row in loc_rows if row[0]]
    
    sports = db.query(SportConfig).order_by(SportConfig.code).all()
    
    return templates.TemplateResponse(
        "traders.html",
        {
            "request": request,
            "traders": traders,
            "sports": sports,
            "locations": locations,
            "selected_location": location_value,
            "search_query": search_value,
            "active_tab": "traders",
        },
    )


@app.get("/traders/{trader_id}/bio", response_class=HTMLResponse, name="trader_bio")
def trader_bio(
    request: Request,
    trader_id: int,
    db: Session = Depends(get_db),
):
    """Trader BIO page route."""
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    return templates.TemplateResponse(
        "trader_bio.html",
        {
            "request": request,
            "trader": trader,
            "active_tab": "traders",
        },
    )


@app.get("/traders/{trader_id}/requests", response_class=HTMLResponse, name="trader_requests")
def trader_requests(
    request: Request,
    trader_id: int,
    db: Session = Depends(get_db),
):
    """Trader Requests page route."""
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")

    requests_q = (
        db.query(TraderRequest)
        .filter(TraderRequest.trader_id == trader_id)
        .order_by(TraderRequest.date_from.desc(), TraderRequest.id.desc())
    )
    requests = requests_q.all()

    return templates.TemplateResponse(
        "trader_requests.html",
        {
            "request": request,
            "trader": trader,
            "requests": requests,
            "active_tab": "traders",
        },
    )


@app.post("/traders/{trader_id}/requests", response_class=HTMLResponse)
def create_trader_request(
    request: Request,
    trader_id: int,
    request_type: str = Form(...),  # "REQUEST_IN", "REQUEST_OFF_DAY", or "REQUEST_OFF_RANGE"
    request_date_from: date = Form(...),
    request_date_to: date = Form(None),
    reason: str = Form(""),
    db: Session = Depends(get_db),
):
    """Create a new trader request."""
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")

    # Validate request_type
    if request_type not in ["REQUEST_IN", "REQUEST_OFF_DAY", "REQUEST_OFF_RANGE"]:
        raise HTTPException(status_code=400, detail="Invalid request_type")

    # Determine effect_type based on request_kind
    if request_type in ["REQUEST_OFF_DAY", "REQUEST_OFF_RANGE"]:
        effect_type = "UNAVAILABLE"
    elif request_type == "REQUEST_IN":
        effect_type = "MANDATORY"
    else:
        raise HTTPException(status_code=400, detail="Invalid request_type")

    # Handle date_to based on request type
    if request_type == "REQUEST_OFF_RANGE":
        if request_date_to is None:
            raise HTTPException(status_code=400, detail="Date To is required for Request Off (Range)")
        if request_date_to < request_date_from:
            raise HTTPException(status_code=400, detail="Date To must be greater than or equal to Date From")
        date_to = request_date_to
    else:
        # For single-day requests, date_to equals date_from
        date_to = request_date_from

    new_req = TraderRequest(
        trader_id=trader_id,
        request_kind=request_type,
        effect_type=effect_type,
        date_from=request_date_from,
        date_to=date_to,
        shift_type=None,
        sport=None,
        reason=reason.strip() or None,
        status="PENDING",
    )

    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    return RedirectResponse(
        url=request.url_for("trader_requests", trader_id=trader_id),
        status_code=303,
    )


# Constants for preferences
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SHIFT_TYPES = ["FULL", "EARLY", "MID", "LATE"]


@app.get("/traders/{trader_id}/preferences", response_class=HTMLResponse, name="trader_preferences")
def trader_preferences(
    request: Request,
    trader_id: int,
    db: Session = Depends(get_db),
):
    """Trader Preferences page route."""
    from sqlalchemy import and_
    
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    # Load weekly pattern rows for this trader
    pattern_rows = (
        db.query(TraderWeeklyPattern)
        .filter(TraderWeeklyPattern.trader_id == trader_id)
        .all()
    )
    
    # If none exist, initialise default indifferent rows (hard_block=False, weight=0)
    if not pattern_rows:
        new_rows = []
        for day_index in range(7):
            for shift_type in SHIFT_TYPES:
                row = TraderWeeklyPattern(
                    trader_id=trader_id,
                    day_of_week=day_index,
                    shift_type=shift_type,
                    hard_block=False,
                    weight=0,
                )
                db.add(row)
                new_rows.append(row)
        db.commit()
        for row in new_rows:
            db.refresh(row)
        pattern_rows = new_rows
    
    # Build a dict[(day_index, shift_type)] -> state_code for template
    # state_code in {"NONE", "IN", "OFF", "BLOCK"}
    cell_states = {}
    for row in pattern_rows:
        key = (row.day_of_week, row.shift_type)
        if row.hard_block:
            state = "BLOCK"
        else:
            if row.weight is None or row.weight == 0:
                state = "NONE"
            elif row.weight > 0:
                state = "IN"
            else:
                state = "OFF"
        cell_states[key] = state
    
    # Days-off grouping preference
    grouping = (
        db.query(TraderPreference)
        .filter(
            TraderPreference.trader_id == trader_id,
            TraderPreference.category == "DAYS_OFF_GROUPING",
            TraderPreference.key == "PREFERENCE",
        )
        .first()
    )
    
    if grouping is None:
        grouping_value = "NONE"   # default
    else:
        if grouping.weight is None or grouping.weight == 0:
            grouping_value = "NONE"
        elif grouping.weight > 0:
            grouping_value = "BACK_TO_BACK"
        else:
            grouping_value = "SPLIT"
    
    return templates.TemplateResponse(
        "trader_preferences.html",
        {
            "request": request,
            "trader": trader,
            "days": DAYS,
            "shift_types": SHIFT_TYPES,
            "cell_states": cell_states,
            "grouping_value": grouping_value,
            "active_tab": "traders",
        },
    )


@app.post("/traders/{trader_id}/preferences", response_class=HTMLResponse)
async def save_trader_preferences(
    request: Request,
    trader_id: int,
    db: Session = Depends(get_db),
):
    """Save trader preferences."""
    from sqlalchemy import and_
    
    form = await request.form()
    
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    # Helper mapping from state string to DB fields
    def state_to_fields(code: str):
        code = (code or "NONE").upper()
        if code == "BLOCK":
            return True, 0
        elif code == "IN":
            return False, 1
        elif code == "OFF":
            return False, -1
        else:
            return False, 0
    
    # Update or create each weekly pattern row
    for day_index in range(7):
        for shift_type in SHIFT_TYPES:
            field_name = f"state_{day_index}_{shift_type}"
            state_code = form.get(field_name, "NONE")
            
            hard_block, weight = state_to_fields(state_code)
            
            row = (
                db.query(TraderWeeklyPattern)
                .filter(
                    TraderWeeklyPattern.trader_id == trader_id,
                    TraderWeeklyPattern.day_of_week == day_index,
                    TraderWeeklyPattern.shift_type == shift_type,
                )
                .first()
            )
            
            if row is None:
                row = TraderWeeklyPattern(
                    trader_id=trader_id,
                    day_of_week=day_index,
                    shift_type=shift_type,
                )
                db.add(row)
            
            row.hard_block = hard_block
            row.weight = weight
    
    # Days-off grouping preference from radio group
    grouping_value = (form.get("days_off_grouping") or "NONE").upper()
    
    if grouping_value == "BACK_TO_BACK":
        grouping_weight = 2
    elif grouping_value == "SPLIT":
        grouping_weight = -2
    else:
        grouping_weight = 0
    
    grouping = (
        db.query(TraderPreference)
        .filter(
            TraderPreference.trader_id == trader_id,
            TraderPreference.category == "DAYS_OFF_GROUPING",
            TraderPreference.key == "PREFERENCE",
        )
        .first()
    )
    if grouping is None:
        grouping = TraderPreference(
            trader_id=trader_id,
            category="DAYS_OFF_GROUPING",
            key="PREFERENCE",
        )
        db.add(grouping)
    
    grouping.weight = grouping_weight
    
    db.commit()
    
    return RedirectResponse(
        url=request.url_for("trader_preferences", trader_id=trader_id),
        status_code=303,
    )


@app.get("/traders/{trader_id}")
def get_trader(trader_id: int, db: Session = Depends(get_db)):
    """Return trader details for BIO modal (JSON API)."""
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if not trader:
        raise HTTPException(status_code=404, detail="Trader not found")

    return {
        "id": trader.id,
        "name": trader.name,
        "alias": trader.alias,
        "manager": trader.manager,
        "level": trader.level,
        "user_role": trader.user_role.value if hasattr(trader.user_role, "value") else trader.user_role,
        "location": trader.location,
        "required_days_per_week": trader.required_days_per_week,
        "hours_per_week": trader.hours_per_week,
        "is_active": trader.is_active,
        "primary_sport": trader.primary_sport,
        "secondary_sport": trader.secondary_sport,
        "sport_skills": [
            {
                "sport_code": skill.sport_code,
                "sport_level": skill.sport_level,
            }
            for skill in (trader.sport_skills or [])
        ],
    }


@app.get("/management", response_class=HTMLResponse)
def management_page(request: Request, db: Session = Depends(get_db)):
    """Management page route."""
    locations = db.query(LocationConfig).order_by(LocationConfig.code).all()
    sports = db.query(SportConfig).order_by(SportConfig.code).all()
    requests = db.query(TraderRequest).order_by(TraderRequest.date_from.desc()).all()
    active_traders = db.query(Trader).filter(Trader.is_active == True).order_by(Trader.name).all()  # noqa: E712
    return templates.TemplateResponse(
        "management.html",
        {
            "request": request,
            "locations": locations,
            "sports": sports,
            "requests": requests,
            "active_traders": active_traders,
        },
    )


@app.get("/management/daily-resources", name="daily_resources_page")
def daily_resources_page():
    """Placeholder route to satisfy template link."""
    return RedirectResponse(url="/management", status_code=303)
