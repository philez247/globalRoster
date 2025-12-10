"""Security utilities for authentication."""
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse

# Session storage (in production, use Redis or database)
active_sessions = {}

SESSION_COOKIE_NAME = "global_roster_session"
SESSION_DURATION_HOURS = 12


def create_session() -> str:
    """Create a new session token."""
    return secrets.token_urlsafe(32)


def verify_session(session_token: str) -> bool:
    """Verify if a session token is valid."""
    if not session_token:
        return False
    session_data = active_sessions.get(session_token)
    if not session_data:
        return False
    # Check if session expired
    if datetime.now() > session_data["expires_at"]:
        del active_sessions[session_token]
        return False
    return True


def add_session(session_token: str):
    """Add a session with 12-hour expiration."""
    expires_at = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    active_sessions[session_token] = {
        "created_at": datetime.now(),
        "expires_at": expires_at,
    }


def remove_session(session_token: str):
    """Remove a session."""
    active_sessions.pop(session_token, None)


def check_credentials(username: str, password: str) -> bool:
    """Check if username and password are correct."""
    correct_username = secrets.compare_digest(username, "globalRoster")
    correct_password = secrets.compare_digest(password, "Moycullen")
    return correct_username and correct_password


def get_session_from_request(request: Request) -> str | None:
    """Get session token from request cookies."""
    return request.cookies.get(SESSION_COOKIE_NAME)


def require_auth(request: Request):
    """Dependency to require authentication. Raises exception if not authenticated."""
    session_token = get_session_from_request(request)
    if not session_token or not verify_session(session_token):
        # Check if this is an API request (JSON) or HTML request
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header or "/api/" in str(request.url):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
            )
        # For HTML requests, raise redirect exception
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
        )
    return True





