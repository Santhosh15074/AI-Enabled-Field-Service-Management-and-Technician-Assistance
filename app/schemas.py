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
