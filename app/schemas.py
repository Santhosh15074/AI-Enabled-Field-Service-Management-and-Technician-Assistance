from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class LoginIn(BaseModel):
    # An email for staff; an email or a phone number for a customer.
    identifier: str
    password: str


class RegisterIn(BaseModel):
    """Customer self-registration only — see app.routes.auth.register. Phone is mandatory;
    email is optional, since not every customer has or checks one. No address: that's
    collected when they raise their first complaint instead."""

    name: str
    phone: str
    password: str
    email: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None
    role: str
    # Customers only — None for staff. Lets the frontend know whether the "raise a
    # complaint" form still needs to ask for an address or if one's already on file.
    address: str | None = None


class CreateStaffUserIn(BaseModel):
    """An admin provisioning a colleague — see app.routes.users.create_staff_user. Customers
    still only sign themselves up through the portal; this never creates one."""

    name: str
    email: str
    password: str
    role: str  # "admin" or "technician"
    skill_area: str | None = None


class SetUserActiveIn(BaseModel):
    is_active: bool


class StaffUserOut(BaseModel):
    id: int
    name: str
    email: str | None
    role: str
    is_active: bool
    created_at: datetime
    skill_area: str | None = None  # technicians only
    phone: str | None = None  # customers only


class AdminOverview(BaseModel):
    customers: int
    technicians: int
    open_requests: int
    critical_equipment: int


class CustomerOverview(BaseModel):
    equipment: int
    open_requests: int
    resolved_requests: int


class TechnicianOverview(BaseModel):
    assigned: int
    in_progress: int
    resolved: int


class EquipmentIn(BaseModel):
    name: str
    type: str
    serial_number: str | None = None


class EquipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    serial_number: str | None
    # From its latest reading — see app.ml.failure.attach_latest_risk. Both None until a
    # technician has recorded a reading at all.
    risk_level: str | None = None
    risk_score: float | None = None


class EquipmentReadingsIn(BaseModel):
    """Sensor readings from a technician's visit — see app.routes.equipment.record_readings,
    which scores them for failure risk as soon as they're saved."""

    quality_grade: str
    air_temperature_k: float
    process_temperature_k: float
    rotational_speed_rpm: float
    torque_nm: float
    tool_wear_min: float


class ServiceRequestIn(BaseModel):
    description: str
    equipment_id: int | None = None
    category_id: int | None = None
    # Only required the first time a customer has no address on file; see
    # app.routes.requests.create_request. Saved to their profile once given.
    address: str | None = None


class ComplaintCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_name: str
    description: str | None


class RequestUpdateIn(BaseModel):
    """Admins may set either field; a technician may only set status, and only on their
    own assigned requests. See app.routes.requests.update_request."""

    technician_id: int | None = None
    status: str | None = None


class TechnicianSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    skill_area: str | None


class CustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str


class AdminEquipmentOut(BaseModel):
    """Every customer's equipment, for the admin fleet-risk view — see
    app.routes.equipment.list_all_equipment. EquipmentOut is a customer's own, narrower view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    serial_number: str | None
    last_service_date: date | None
    risk_level: str | None = None
    risk_score: float | None = None
    customer: CustomerSummary


class ServiceRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    status: str
    urgency: str
    created_at: datetime
    equipment: EquipmentOut | None
    category: ComplaintCategoryOut | None
    customer: CustomerSummary
    technician: TechnicianSummary | None


class KnowledgeBaseEntryIn(BaseModel):
    """Full contents of one troubleshooting entry — see app.routes.knowledge_base, which uses
    this for both creating and replacing an entry."""

    category_id: int
    equipment_type: str | None = None
    issue_pattern: str
    suggested_fix: str


class KnowledgeBaseEntryOut(BaseModel):
    id: int
    category_id: int
    category_name: str
    equipment_type: str | None
    issue_pattern: str
    suggested_fix: str


class SuggestionIn(BaseModel):
    """A description to match against the knowledge base — see app.ml.troubleshooting. Used
    before a request even exists, so a customer can try a quick fix while typing their
    complaint."""

    description: str


class SuggestionOut(BaseModel):
    equipment_type: str | None
    issue_pattern: str
    suggested_fix: str
    # 0-1: how closely this entry matched the description, not a probability.
    similarity: float


class ReportExtractIn(BaseModel):
    """A report's free text, for a preview of what app.report_extraction would guess — not
    saved. See app.routes.service_reports.extract_report."""

    report_text: str


class ExtractedFieldsOut(BaseModel):
    issue: str | None
    action_taken: str | None
    parts_used: str | None
    time_spent_minutes: int | None


class ServiceReportIn(BaseModel):
    """What's actually saved: the free text plus whatever the technician confirmed or corrected
    from the extraction preview — any of the structured fields may be left blank if extraction
    couldn't guess it and the technician didn't fill it in either."""

    report_text: str
    issue: str | None = None
    action_taken: str | None = None
    parts_used: str | None = None
    time_spent_minutes: int | None = None


class ServiceReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    report_text: str
    issue: str | None
    action_taken: str | None
    parts_used: str | None
    time_spent_minutes: int | None
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    link: str | None
    status: str
    sent_on: datetime


class UnreadCountOut(BaseModel):
    count: int
