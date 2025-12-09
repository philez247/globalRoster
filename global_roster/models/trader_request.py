"""Trader request model."""
from datetime import date, datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func as sa_func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from global_roster.models.base import Base


class TraderRequestKind(str, Enum):
    """Request kind enum."""
    REQUEST_IN = "REQUEST_IN"
    REQUEST_OFF_DAY = "REQUEST_OFF_DAY"
    REQUEST_OFF_RANGE = "REQUEST_OFF_RANGE"
    # Legacy values (kept for backward compatibility)
    REQUEST_OFF_PAID = "REQUEST_OFF_PAID"
    REQUEST_OFF_FREE = "REQUEST_OFF_FREE"
    LEAVE_RANGE = "LEAVE_RANGE"


class TraderRequestEffectType(str, Enum):
    """Effect type enum for how requests behave in allocation."""
    MANDATORY = "MANDATORY"  # must work
    UNAVAILABLE = "UNAVAILABLE"  # cannot work
    SOFT_PREFERENCE = "SOFT_PREFERENCE"  # strong preference only (not used for REQUEST_IN/OFF_DAY/OFF_RANGE)


class TraderRequestStatus(str, Enum):
    """Request status enum."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TraderRequest(Base):
    """Trader request model for managing trader scheduling requests."""
    
    __tablename__ = "trader_requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trader_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("traders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # what the trader is asking for
    request_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    """
    Allowed values (see TraderRequestKind enum):
    - REQUEST_IN
    - REQUEST_OFF_DAY
    - REQUEST_OFF_RANGE
    - Legacy: REQUEST_OFF_PAID, REQUEST_OFF_FREE, LEAVE_RANGE
    """
    
    # how it behaves in the allocation engine (once approved)
    effect_type: Mapped[str] = mapped_column(String(50), nullable=False)
    """
    Allowed values (see TraderRequestEffectType enum):
    - MANDATORY          # must work (for REQUEST_IN)
    - UNAVAILABLE        # cannot work (for REQUEST_OFF_DAY, REQUEST_OFF_RANGE)
    - SOFT_PREFERENCE    # strong preference only (legacy, not used for main request kinds)
    """
    
    # date or date range
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)  # equal to date_from for single-day requests
    
    # optional scope (nullable means "whole day")
    shift_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # FULL, EARLY, MID, LATE, HALF_AM, HALF_PM
    sport_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # leave-specific field (optional)
    leave_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # ANNUAL, SICK, OTHER
    
    # free text for managers
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # approval workflow
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    """
    Status values (see TraderRequestStatus enum):
    - PENDING
    - APPROVED
    - REJECTED
    """
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=sa_func.now())
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    trader: Mapped["Trader"] = relationship("Trader", backref="requests")



