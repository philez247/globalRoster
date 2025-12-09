"""Trader request Pydantic schemas."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from global_roster.models.trader_request import (
    TraderRequestKind,
    TraderRequestEffectType,
    TraderRequestStatus,
)


class TraderRequestBase(BaseModel):
    """Base trader request schema with common fields."""
    request_kind: str
    date_from: date
    date_to: date
    shift_type: Optional[str] = None
    sport_code: Optional[str] = None
    destination: Optional[str] = None
    leave_type: Optional[str] = None
    reason: Optional[str] = None


class TraderRequestCreate(TraderRequestBase):
    """Schema for creating a trader request.
    
    Note: effect_type is NOT included here - it is derived from request_kind
    by the service layer. Client should not provide effect_type.
    """
    pass


class TraderRequestUpdate(BaseModel):
    """Schema for updating a trader request.
    
    Note: effect_type is NOT included here - it is derived from request_kind
    by the service layer. Client should not provide effect_type.
    """
    request_kind: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    shift_type: Optional[str] = None
    sport_code: Optional[str] = None
    destination: Optional[str] = None
    leave_type: Optional[str] = None
    reason: Optional[str] = None


class TraderRequestRead(TraderRequestBase):
    """Schema for reading a trader request (includes id, status, effect_type, created_at, approved_by, approved_at).
    
    Note: effect_type is included in the response so the UI can display it,
    but it is derived from request_kind and not controlled by the client.
    """
    id: int
    effect_type: str  # Included for display, but derived from request_kind
    status: str
    created_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

