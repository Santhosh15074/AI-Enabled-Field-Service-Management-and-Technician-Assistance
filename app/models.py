"""Database tables.

The ten tables from the First Review report, plus request_status_log, which records every
status change of a service request (slide 6 of the presentation).

Owned records use ON DELETE CASCADE: deleting a user removes their customer or technician
profile, and deleting a customer removes their equipment and requests. References that are
not ownership use ON DELETE SET NULL instead, so that deleting a technician or a category
does not delete a customer's service history.
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(enum.StrEnum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    TECHNICIAN = "technician"


class Urgency(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequestStatus(enum.StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class Availability(enum.StrEnum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFF_DUTY = "off_duty"


class RiskLevel(enum.StrEnum):
    GOOD = "good"
    MODERATE = "moderate"
    CRITICAL = "critical"


class NotificationStatus(enum.StrEnum):
    UNREAD = "unread"
    READ = "read"


def _one_of(column: str, values: type[enum.StrEnum]) -> CheckConstraint:
    allowed = ", ".join(f"'{v.value}'" for v in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=f"{column}_valid")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (_one_of("role", Role),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(60))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped["Customer | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    technician: Mapped["Technician | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(20))

    user: Mapped[User] = relationship(back_populates="customer")
    equipment: Mapped[list["Equipment"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", passive_deletes=True
    )


class Technician(Base):
    __tablename__ = "technicians"
    __table_args__ = (_one_of("availability", Availability),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    skill_area: Mapped[str | None] = mapped_column(String(100))
    availability: Mapped[str] = mapped_column(String(20), default=Availability.AVAILABLE)

    user: Mapped[User] = relationship(back_populates="technician")


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (CheckConstraint("quality_grade IN ('L', 'M', 'H')", name="quality_grade_valid"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50))
    serial_number: Mapped[str | None] = mapped_column(String(100))
    install_date: Mapped[date | None] = mapped_column(Date)
    last_service_date: Mapped[date | None] = mapped_column(Date)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # Readings a technician records on each visit. They match the AI4I 2020 features, so the
    # failure-prediction model (Phase 6) can score this equipment.
    quality_grade: Mapped[str | None] = mapped_column(String(1))
    air_temperature_k: Mapped[float | None] = mapped_column(Float)
    process_temperature_k: Mapped[float | None] = mapped_column(Float)
    rotational_speed_rpm: Mapped[float | None] = mapped_column(Float)
    torque_nm: Mapped[float | None] = mapped_column(Float)
    tool_wear_min: Mapped[float | None] = mapped_column(Float)

    customer: Mapped[Customer] = relationship(back_populates="equipment")


class ComplaintCategory(Base):
    __tablename__ = "complaint_categories"
    __table_args__ = (_one_of("urgency_level", Urgency),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    # Default urgency for the category; each request also stores its own predicted urgency.
    urgency_level: Mapped[str] = mapped_column(String(10), default=Urgency.MEDIUM)


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    __table_args__ = (_one_of("status", RequestStatus), _one_of("urgency", Urgency))

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id", ondelete="SET NULL"))
    technician_id: Mapped[int | None] = mapped_column(
        ForeignKey("technicians.id", ondelete="SET NULL"), index=True
    )
    category_id: Mapped[int | None] = mapped_column(ForeignKey("complaint_categories.id", ondelete="SET NULL"))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=RequestStatus.OPEN)
    urgency: Mapped[str] = mapped_column(String(10), default=Urgency.MEDIUM)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RequestStatusLog(Base):
    __tablename__ = "request_status_log"
    __table_args__ = (_one_of("new_status", RequestStatus),)

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_requests.id", ondelete="CASCADE"), index=True)
    old_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20))
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    note: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeBaseEntry(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("complaint_categories.id", ondelete="CASCADE"), index=True
    )
    equipment_type: Mapped[str | None] = mapped_column(String(50))
    issue_pattern: Mapped[str] = mapped_column(Text)
    suggested_fix: Mapped[str] = mapped_column(Text)


class ServiceReport(Base):
    __tablename__ = "service_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE"), unique=True
    )
    report_text: Mapped[str] = mapped_column(Text)
    # Fields extracted from report_text in Phase 5; the technician can correct them before saving.
    issue: Mapped[str | None] = mapped_column(Text)
    action_taken: Mapped[str | None] = mapped_column(Text)
    parts_used: Mapped[str | None] = mapped_column(Text)
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PredictionLog(Base):
    __tablename__ = "prediction_log"
    __table_args__ = (_one_of("risk_level", RiskLevel),)

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"), index=True)
    predicted_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(10))


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (_one_of("status", NotificationStatus),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    message: Mapped[str] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(10), default=NotificationStatus.UNREAD)
    sent_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
