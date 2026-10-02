from pydantic import BaseModel, ConfigDict


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
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
