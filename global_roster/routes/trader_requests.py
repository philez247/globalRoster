"""Trader requests router."""
from datetime import date as date_type
from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from global_roster.core.config import TEMPLATES_DIR
from global_roster.core.db import get_db
from global_roster.models.trader_request import TraderRequest
from global_roster.schemas.trader_request import TraderRequestCreate, TraderRequestRead
from global_roster.services import trader_request_service, trader_service

router = APIRouter(tags=["Trader Requests"])
api_router = APIRouter(prefix="/api", tags=["Trader Requests API"])

# Configure Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/traders/{trader_id}/requests", response_class=HTMLResponse)
def list_trader_requests(
    request: Request,
    trader_id: int,
    db: Session = Depends(get_db),
    error_message: str | None = None,
):
    """List all requests for a trader and show add-request form."""
    # Verify trader exists
    trader = trader_service.get(db, trader_id)
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    # Get all requests for this trader
    requests = trader_request_service.get_requests_for_trader(db, trader_id)
    
    return templates.TemplateResponse(
        "trader_requests.html",
        {
            "request": request,
            "trader": trader,
            "requests": requests,
            "error_message": error_message,
        }
    )


@router.get("/traders/{trader_id}/requests/inner", response_class=HTMLResponse)
def trader_requests_inner(
    trader_id: int,
    request: Request,
    db: Session = Depends(get_db),
    mode: str = "edit",
):
    """Get inner HTML for requests modal."""
    trader = trader_service.get(db, trader_id)
    if not trader:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    requests_list = trader_request_service.get_requests_for_trader(db, trader_id)
    
    return templates.TemplateResponse(
        "partials/_trader_requests_inner.html",
        {
            "request": request,
            "trader": trader,
            "requests": requests_list,
            "mode": mode,
        },
    )


@router.post("/traders/{trader_id}/requests")
def create_trader_request(
    request: Request,
    trader_id: int,
    request_kind: str = Form(...),
    date_from: str = Form(...),
    date_to: str | None = Form(None),
    shift_type: str | None = Form(None),
    sport_code: str | None = Form(None),
    reason: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Create a new trader request from form data."""
    # Verify trader exists
    trader = trader_service.get(db, trader_id)
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    # Parse dates
    try:
        date_from_parsed = date_type.fromisoformat(date_from)
        # For single-day requests, date_to may not be provided or empty
        if date_to and date_to.strip():
            date_to_parsed = date_type.fromisoformat(date_to)
        else:
            date_to_parsed = date_from_parsed
    except ValueError:
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header or request.headers.get("x-requested-with") == "XMLHttpRequest":
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Invalid date format"}, status_code=400)
        return templates.TemplateResponse(
            "trader_requests.html",
            {
                "request": request,
                "trader": trader,
                "requests": trader_request_service.get_requests_for_trader(db, trader_id),
                "error_message": "Invalid date format",
            },
            status_code=400,
        )
    
    # Normalize values based on request_kind
    if request_kind == "REQUEST_IN":
        # REQUEST_IN: enforce single-day, keep sport_code / shift_type
        date_to_parsed = date_from_parsed
        shift_type_clean = shift_type.strip() if shift_type and shift_type.strip() else None
        sport_code_clean = sport_code.strip() if sport_code and sport_code.strip() else None
    elif request_kind == "REQUEST_OFF_DAY":
        # REQUEST_OFF_DAY: enforce single-day, force sport_code = None, shift_type = None
        date_to_parsed = date_from_parsed
        shift_type_clean = None
        sport_code_clean = None
    elif request_kind == "REQUEST_OFF_RANGE":
        # REQUEST_OFF_RANGE: ensure date_to >= date_from, force sport_code = None, shift_type = None
        if date_to_parsed < date_from_parsed:
            accept_header = request.headers.get("accept", "")
            if "application/json" in accept_header or request.headers.get("x-requested-with") == "XMLHttpRequest":
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail": "Date To must be greater than or equal to Date From"}, status_code=400)
            return templates.TemplateResponse(
                "trader_requests.html",
                {
                    "request": request,
                    "trader": trader,
                    "requests": trader_request_service.get_requests_for_trader(db, trader_id),
                    "error_message": "Date To must be greater than or equal to Date From",
                },
                status_code=400,
            )
        shift_type_clean = None
        sport_code_clean = None
    else:
        # Fallback for any other values
        shift_type_clean = shift_type.strip() if shift_type and shift_type.strip() else None
        sport_code_clean = sport_code.strip() if sport_code and sport_code.strip() else None
    
    # Normalize empty strings to None for reason
    reason_clean = reason.strip() if reason and reason.strip() else None
    
    # Create request schema (effect_type is not included - it's derived by the service)
    request_data = TraderRequestCreate(
        request_kind=request_kind,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        shift_type=shift_type_clean,
        sport_code=sport_code_clean,
        destination=None,  # No longer used in form
        leave_type=None,  # No longer used
        reason=reason_clean,
    )
    
    # Create request (effect_type will be auto-derived from request_kind)
    trader_request_service.create_request(db, trader_id, request_data)
    
    # Check if this is an AJAX request
    accept_header = request.headers.get("accept", "")
    if "application/json" in accept_header or request.headers.get("x-requested-with") == "XMLHttpRequest":
        from fastapi.responses import JSONResponse
        return JSONResponse({"status": "ok"})
    
    return RedirectResponse(
        url=f"/traders/{trader_id}/requests",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/trader-requests/{request_id}/approve", response_class=RedirectResponse)
def approve_trader_request(
    request_id: int,
    db: Session = Depends(get_db),
    manager_name: str = Form("Manager"),  # Default manager name, can be enhanced later
):
    """Approve a trader request."""
    request_obj = db.query(TraderRequest).filter(
        TraderRequest.id == request_id
    ).first()
    
    if request_obj is None:
        raise HTTPException(status_code=404, detail="Request not found")
    
    trader_id = request_obj.trader_id
    trader_request_service.approve_request(db, request_id, manager_name)
    
    return RedirectResponse(
        url=f"/traders/{trader_id}/requests",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/trader-requests/{request_id}/reject", response_class=RedirectResponse)
def reject_trader_request(
    request_id: int,
    db: Session = Depends(get_db),
    manager_name: str = Form("Manager"),  # Default manager name, can be enhanced later
):
    """Reject a trader request."""
    request_obj = db.query(TraderRequest).filter(
        TraderRequest.id == request_id
    ).first()
    
    if request_obj is None:
        raise HTTPException(status_code=404, detail="Request not found")
    
    trader_id = request_obj.trader_id
    trader_request_service.reject_request(db, request_id, manager_name)
    
    return RedirectResponse(
        url=f"/traders/{trader_id}/requests",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/trader-requests/{request_id}/delete")
def delete_trader_request(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db),
):
    """Delete a trader request."""
    request_obj = db.query(TraderRequest).filter(
        TraderRequest.id == request_id
    ).first()
    
    if request_obj is None:
        raise HTTPException(status_code=404, detail="Request not found")
    
    trader_id = request_obj.trader_id
    trader_request_service.delete_request(db, request_id)
    
    # Check if this is an AJAX request
    accept_header = request.headers.get("accept", "")
    if "application/json" in accept_header or request.headers.get("x-requested-with") == "XMLHttpRequest":
        from fastapi.responses import JSONResponse
        return JSONResponse({"status": "ok"})
    
    return RedirectResponse(
        url=f"/traders/{trader_id}/requests",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ============================================================================
# JSON API Endpoints for Modal
# ============================================================================

@api_router.get("/traders/{trader_id}/requests", response_model=list[TraderRequestRead])
def get_trader_requests_json(
    trader_id: int,
    db: Session = Depends(get_db),
):
    """Get all requests for a trader as JSON."""
    trader = trader_service.get(db, trader_id)
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    requests = trader_request_service.get_requests_for_trader(db, trader_id)
    return requests


@api_router.post("/traders/{trader_id}/requests", response_model=TraderRequestRead)
def create_trader_request_json(
    trader_id: int,
    request_kind: str = Body(...),
    date_from: str = Body(...),
    date_to: str | None = Body(None),
    shift_type: str | None = Body(None),
    sport_code: str | None = Body(None),
    reason: str | None = Body(None),
    db: Session = Depends(get_db),
):
    """Create a new trader request from JSON data."""
    # Verify trader exists
    trader = trader_service.get(db, trader_id)
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    # Parse dates
    try:
        date_from_parsed = date_type.fromisoformat(date_from)
        # For single-day requests, date_to may not be provided or empty
        if date_to and date_to.strip():
            date_to_parsed = date_type.fromisoformat(date_to)
        else:
            date_to_parsed = date_from_parsed
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Normalize values based on request_kind
    if request_kind == "REQUEST_IN":
        # REQUEST_IN: enforce single-day, keep sport_code / shift_type
        date_to_parsed = date_from_parsed
        shift_type_clean = shift_type.strip() if shift_type and shift_type.strip() else None
        sport_code_clean = sport_code.strip() if sport_code and sport_code.strip() else None
    elif request_kind == "REQUEST_OFF_DAY":
        # REQUEST_OFF_DAY: enforce single-day, force sport_code = None, shift_type = None
        date_to_parsed = date_from_parsed
        shift_type_clean = None
        sport_code_clean = None
    elif request_kind == "REQUEST_OFF_RANGE":
        # REQUEST_OFF_RANGE: ensure date_to >= date_from, force sport_code = None, shift_type = None
        if date_to_parsed < date_from_parsed:
            raise HTTPException(status_code=400, detail="Date To must be greater than or equal to Date From")
        shift_type_clean = None
        sport_code_clean = None
    else:
        # Fallback for any other values
        shift_type_clean = shift_type.strip() if shift_type and shift_type.strip() else None
        sport_code_clean = sport_code.strip() if sport_code and sport_code.strip() else None
    
    # Normalize empty strings to None for reason
    reason_clean = reason.strip() if reason and reason.strip() else None
    
    # Create request schema (effect_type is not included - it's derived by the service)
    request_data = TraderRequestCreate(
        request_kind=request_kind,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        shift_type=shift_type_clean,
        sport_code=sport_code_clean,
        destination=None,  # No longer used in form
        leave_type=None,  # No longer used
        reason=reason_clean,
    )
    
    # Create request (effect_type will be auto-derived from request_kind)
    created_request = trader_request_service.create_request(db, trader_id, request_data)
    return created_request


@api_router.post("/trader-requests/{request_id}/cancel")
def cancel_trader_request_json(
    request_id: int,
    db: Session = Depends(get_db),
):
    """Cancel/delete a trader request (JSON endpoint)."""
    request_obj = db.query(TraderRequest).filter(
        TraderRequest.id == request_id
    ).first()
    
    if request_obj is None:
        raise HTTPException(status_code=404, detail="Request not found")
    
    trader_request_service.delete_request(db, request_id)
    return JSONResponse({"status": "ok"})

