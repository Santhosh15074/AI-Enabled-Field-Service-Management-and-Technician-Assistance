"""A technician's write-up of what they found and did on a service request — see
ServiceReport. One per request: see create_report's 400 if it already has one.
"""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Role, ServiceReport, ServiceRequest, User
from app.report_extraction import extract_fields
from app.schemas import ExtractedFieldsOut, ReportExtractIn, ServiceReportIn, ServiceReportOut

router = APIRouter(prefix="/api/requests", tags=["reports"])


def _get_request_for(request_id: int, user: User, db: Session) -> ServiceRequest:
    request = db.get(ServiceRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="That service request doesn't exist.")
    if user.role == Role.TECHNICIAN and request.technician_id != user.technician.id:
        raise HTTPException(status_code=403, detail="This request isn't assigned to you.")
    if user.role == Role.CUSTOMER and request.customer_id != user.customer.id:
        raise HTTPException(status_code=403, detail="That isn't your service request.")
    return request


@router.post("/{request_id}/report/extract", response_model=ExtractedFieldsOut)
def extract_report(
    request_id: int,
    body: ReportExtractIn,
    user: User = Depends(require_role(Role.ADMIN, Role.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    """A preview only — nothing is saved. The technician reviews and can correct every field
    before submitting them for real via create_report."""
    _get_request_for(request_id, user, db)
    return asdict(extract_fields(body.report_text))


@router.post("/{request_id}/report", response_model=ServiceReportOut, status_code=201)
def create_report(
    request_id: int,
    body: ServiceReportIn,
    user: User = Depends(require_role(Role.ADMIN, Role.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    request = _get_request_for(request_id, user, db)
    if db.scalar(select(ServiceReport).where(ServiceReport.request_id == request.id)) is not None:
        raise HTTPException(status_code=400, detail="This request already has a report.")

    report_text = body.report_text.strip()
    if not report_text:
        raise HTTPException(status_code=400, detail="The report can't be empty.")

    report = ServiceReport(
        request_id=request.id,
        report_text=report_text,
        issue=(body.issue or "").strip() or None,
        action_taken=(body.action_taken or "").strip() or None,
        parts_used=(body.parts_used or "").strip() or None,
        time_spent_minutes=body.time_spent_minutes,
    )
    db.add(report)
    db.commit()
    return report


@router.get("/{request_id}/report", response_model=ServiceReportOut)
def get_report(
    request_id: int,
    user: User = Depends(require_role(Role.ADMIN, Role.TECHNICIAN, Role.CUSTOMER)),
    db: Session = Depends(get_db),
):
    request = _get_request_for(request_id, user, db)
    report = db.scalar(select(ServiceReport).where(ServiceReport.request_id == request.id))
    if report is None:
        raise HTTPException(status_code=404, detail="This request doesn't have a report yet.")
    return report
