"""Trader request service layer for business logic."""
from datetime import date, datetime
from typing import List
from sqlalchemy.orm import Session, joinedload

from global_roster.models.trader_request import (
    TraderRequest,
    TraderRequestKind,
    TraderRequestEffectType,
    TraderRequestStatus,
)
from global_roster.schemas.trader_request import TraderRequestCreate, TraderRequestUpdate


def _derive_effect_type(request_kind: str) -> str:
    """Derive effect_type from request_kind according to business rules.
    
    Business rules:
    - REQUEST_OFF_DAY and REQUEST_OFF_RANGE must always have effect_type = UNAVAILABLE
    - REQUEST_IN must always have effect_type = MANDATORY
    
    Args:
        request_kind: The request kind string
        
    Returns:
        The derived effect_type string
        
    Raises:
        ValueError: If request_kind is not supported
    """
    if request_kind in (TraderRequestKind.REQUEST_OFF_DAY, TraderRequestKind.REQUEST_OFF_RANGE):
        return TraderRequestEffectType.UNAVAILABLE
    elif request_kind == TraderRequestKind.REQUEST_IN:
        return TraderRequestEffectType.MANDATORY
    else:
        # For legacy values, default to UNAVAILABLE
        # This maintains backward compatibility
        return TraderRequestEffectType.UNAVAILABLE


def get_requests_for_trader(db: Session, trader_id: int) -> list[TraderRequest]:
    """Get all requests for a trader, ordered by date_from descending."""
    return (
        db.query(TraderRequest)
        .filter(TraderRequest.trader_id == trader_id)
        .order_by(TraderRequest.date_from.desc(), TraderRequest.created_at.desc())
        .all()
    )


def get_approved_requests_for_trader(
    db: Session,
    trader_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[TraderRequest]:
    """Get APPROVED requests for a trader, optionally filtered by date range.
    
    This is used by the availability layer, which only considers APPROVED requests.
    PENDING and REJECTED requests are ignored for availability calculations.
    
    Args:
        db: Database session
        trader_id: Trader ID
        date_from: Optional start date filter
        date_to: Optional end date filter
        
    Returns:
        List of approved TraderRequest objects
    """
    query = (
        db.query(TraderRequest)
        .filter(
            TraderRequest.trader_id == trader_id,
            TraderRequest.status == TraderRequestStatus.APPROVED,
        )
    )
    
    if date_from:
        query = query.filter(TraderRequest.date_to >= date_from)
    if date_to:
        query = query.filter(TraderRequest.date_from <= date_to)
    
    return query.order_by(TraderRequest.date_from.asc()).all()


def create_request(db: Session, trader_id: int, req: TraderRequestCreate, created_by: str | None = None) -> TraderRequest:
    """Create a new trader request.
    
    Auto-sets effect_type based on request_kind using business rules:
    - REQUEST_IN → MANDATORY
    - REQUEST_OFF_DAY → UNAVAILABLE
    - REQUEST_OFF_RANGE → UNAVAILABLE
    
    Note: effect_type from client input is ignored - it is always derived from request_kind.
    
    Inserts request with status="PENDING".
    """
    # Derive effect_type from request_kind (ignore any client-provided effect_type)
    effect_type = _derive_effect_type(req.request_kind)
    
    # Create request
    request = TraderRequest(
        trader_id=trader_id,
        request_kind=req.request_kind,
        effect_type=effect_type,
        date_from=req.date_from,
        date_to=req.date_to,
        shift_type=req.shift_type,
        sport_code=req.sport_code,
        destination=req.destination,
        leave_type=req.leave_type,
        reason=req.reason,
        status=TraderRequestStatus.PENDING,
        created_by=created_by,
    )
    
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def update_request(
    db: Session,
    request_id: int,
    req: TraderRequestUpdate,
) -> TraderRequest | None:
    """Update a trader request.
    
    If request_kind is updated, effect_type is automatically re-derived.
    Note: effect_type from client input is ignored - it is always derived from request_kind.
    """
    request = db.query(TraderRequest).filter(TraderRequest.id == request_id).first()
    if request is None:
        return None
    
    # Update fields
    if req.request_kind is not None:
        request.request_kind = req.request_kind
        # Re-derive effect_type when request_kind changes
        request.effect_type = _derive_effect_type(req.request_kind)
    if req.date_from is not None:
        request.date_from = req.date_from
    if req.date_to is not None:
        request.date_to = req.date_to
    if req.shift_type is not None:
        request.shift_type = req.shift_type
    if req.sport_code is not None:
        request.sport_code = req.sport_code
    if req.destination is not None:
        request.destination = req.destination
    if req.leave_type is not None:
        request.leave_type = req.leave_type
    if req.reason is not None:
        request.reason = req.reason
    
    db.commit()
    db.refresh(request)
    return request


def approve_request(db: Session, request_id: int, manager_name: str) -> TraderRequest | None:
    """Approve a trader request by setting status=APPROVED."""
    request = db.query(TraderRequest).filter(TraderRequest.id == request_id).first()
    if request is None:
        return None
    
    # Ensure effect_type is still consistent with request_kind
    request.effect_type = _derive_effect_type(request.request_kind)
    request.status = TraderRequestStatus.APPROVED
    request.approved_at = datetime.now()
    request.approved_by = manager_name
    
    db.commit()
    db.refresh(request)
    return request


def reject_request(db: Session, request_id: int, manager_name: str) -> TraderRequest | None:
    """Reject a trader request by setting status=REJECTED."""
    request = db.query(TraderRequest).filter(TraderRequest.id == request_id).first()
    if request is None:
        return None
    
    request.status = TraderRequestStatus.REJECTED
    request.approved_at = datetime.now()
    request.approved_by = manager_name
    
    db.commit()
    db.refresh(request)
    return request


def delete_request(db: Session, request_id: int) -> bool:
    """Delete a trader request."""
    request = db.query(TraderRequest).filter(TraderRequest.id == request_id).first()
    if request is None:
        return False
    
    db.delete(request)
    db.commit()
    return True


def get_all_requests_with_trader(db: Session) -> List[TraderRequest]:
    """
    Return all TraderRequest rows, eager-loading the related Trader
    so the management view can show name, alias, location.
    """
    return (
        db.query(TraderRequest)
        .options(joinedload(TraderRequest.trader))
        .order_by(TraderRequest.date_from, TraderRequest.date_to, TraderRequest.id)
        .all()
    )

