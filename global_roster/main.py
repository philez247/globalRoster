"""Main FastAPI application."""
import secrets
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from global_roster.core.config import TEMPLATES_DIR, STATIC_DIR
from global_roster.routes import config, management, traders as traders_router, trader_requests

security = HTTPBasic()


def check_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "globalRoster")
    correct_password = secrets.compare_digest(credentials.password, "Moycullen")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


app = FastAPI(title="Global Roster", dependencies=[Depends(check_credentials)])

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers
app.include_router(traders_router.router)
app.include_router(traders_router.api_router)
app.include_router(management.router)
app.include_router(trader_requests.router)
app.include_router(trader_requests.api_router)
app.include_router(config.router)


@app.get("/", response_class=HTMLResponse)
def read_home(request: Request):
    """Home page route."""
    return templates.TemplateResponse("home.html", {"request": request})

