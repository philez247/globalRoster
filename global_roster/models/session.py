"""Session model for authentication."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String

from global_roster.models.base import Base


class Session(Base):
    """Session model for storing authentication sessions."""
    __tablename__ = "sessions"

    token = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

