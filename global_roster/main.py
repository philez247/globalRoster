"""Main FastAPI application."""
from fastapi import Depends, FastAPI, Form, Request, status, HTTPException
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
def traders_page(request: Request, db: Session = Depends(get_db)):
    """Traders page route."""
    traders = db.query(Trader).order_by(Trader.name).all()
    sports = db.query(SportConfig).order_by(SportConfig.code).all()
    return templates.TemplateResponse(
        "traders.html",
        {"request": request, "traders": traders, "sports": sports},
    )


@app.get("/traders/{trader_id}")
def get_trader(trader_id: int, db: Session = Depends(get_db)):
    """Return trader details for BIO modal."""
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
