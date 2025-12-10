"""Security utilities for authentication."""
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DBSession

from global_roster.models.session import Session as SessionModel

SESSION_COOKIE_NAME = "global_roster_session"
SESSION_DURATION_HOURS = 12


def create_session() -> str:
    """Create a new session token."""
    return secrets.token_urlsafe(32)


def verify_session(session_token: str, db: DBSession) -> bool:
    """Verify if a session token is valid."""
    if not session_token:
        return False
    
    # Query database for session
    session = db.query(SessionModel).filter(SessionModel.token == session_token).first()
    if not session:
        return False
    
    # Check if session expired
    if datetime.now() > session.expires_at:
        # Remove expired session
        db.delete(session)
        db.commit()
        return False
    
    return True


def add_session(session_token: str, db: DBSession):
    """Add a session with 12-hour expiration."""
    expires_at = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    session = SessionModel(
        token=session_token,
        created_at=datetime.now(),
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()


def remove_session(session_token: str, db: DBSession):
    """Remove a session."""
    session = db.query(SessionModel).filter(SessionModel.token == session_token).first()
    if session:
        db.delete(session)
        db.commit()


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





