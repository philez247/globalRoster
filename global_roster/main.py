"""Main FastAPI application."""
from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from global_roster.core.config import TEMPLATES_DIR, STATIC_DIR
from global_roster.core.security import (
    SESSION_COOKIE_NAME,
    SESSION_DURATION_HOURS,
    add_session,
    check_credentials,
    create_session,
    get_session_from_request,
    verify_session,
)

app = FastAPI(title="Global Roster")


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to check authentication for protected routes."""
    
    # Routes that don't require authentication
    PUBLIC_ROUTES = ["/login", "/static", "/docs", "/openapi.json", "/redoc"]
    
    async def dispatch(self, request: Request, call_next):
        # Check if route is public
        path = request.url.path
        is_public = any(path.startswith(route) for route in self.PUBLIC_ROUTES)
        
        if not is_public:
            # Check authentication
            session_token = get_session_from_request(request)
            if not session_token or not verify_session(session_token):
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
        
        response = await call_next(request)
        return response


app.add_middleware(AuthMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers (authentication handled by middleware)
app.include_router(traders_router.router)
app.include_router(traders_router.api_router)
app.include_router(management.router)
app.include_router(trader_requests.router)
app.include_router(trader_requests.api_router)
app.include_router(config.router)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
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
    add_session(session_token)
    
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
def logout(request: Request):
    """Handle logout and clear session cookie."""
    from global_roster.core.security import get_session_from_request, remove_session
    
    session_token = get_session_from_request(request)
    if session_token:
        remove_session(session_token)
    
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response


@app.get("/", response_class=HTMLResponse)
def read_home(request: Request):
    """Home page route."""
    return templates.TemplateResponse("home.html", {"request": request})

