"""Database tables.

The ten tables from the First Review report, plus request_status_log, which records every
status change of a service request (slide 6 of the presentation), and shops.

Every user belongs to one shop, and a shop's customers, technicians, equipment and requests are
only ever visible to that shop's own staff — see app.shops for the queries that enforce it.
Complaint categories are shared reference data; knowledge-base entries belong to a shop, since
its admin edits them.

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


class VoiceNoteStatus(enum.StrEnum):
    PENDING = "pending"  # uploaded, waiting for its turn to be transcribed
    TRANSCRIBING = "transcribing"
    DONE = "done"
    FAILED = "failed"


class Plan(enum.StrEnum):
    STARTER = "starter"
    GROWTH = "growth"
    PRO = "pro"


# (technicians, reports a month) each plan includes — founder/pricing.md. A shop's own limits start
# from these and can be changed one shop at a time in the config portal.
PLAN_LIMITS = {Plan.STARTER: (10, 750), Plan.GROWTH: (25, 2000), Plan.PRO: (50, 4000)}


def _one_of(column: str, values: type[enum.StrEnum]) -> CheckConstraint:
    allowed = ", ".join(f"'{v.value}'" for v in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=f"{column}_valid")


class Shop(Base):
    """One customer business: an AC or appliance service shop with its own staff and customers.
    Set up and configured only by a Sollu operator, in the config portal (app.routes.platform)."""

    __tablename__ = "shops"
    __table_args__ = (_one_of("plan", Plan),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    # Short and URL-safe, for the shop's own customer sign-up link: /portal/register?shop=<slug>.
    slug: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    # A deactivated shop's staff and customers can't log in, and its sign-up link stops working.
    is_active: Mapped[bool] = mapped_column(default=True)
    plan: Mapped[str] = mapped_column(String(20), default=Plan.STARTER)
    # Enforced: an owner can't add or reactivate a technician past this.
    technician_limit: Mapped[int] = mapped_column(Integer, default=PLAN_LIMITS[Plan.STARTER][0])
    # Not enforced (the plan promises no overage charges); shown in the config portal so the
    # operator can call a shop that keeps going over.
    monthly_report_limit: Mapped[int] = mapped_column(Integer, default=PLAN_LIMITS[Plan.STARTER][1])
    # Who the operator calls about the shop; usually the owner's mobile.
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Operator(Base):
    """A Sollu staff member who sets up and configures shops in the config portal. Entirely
    separate from shop accounts (User): its own table, login and cookie, and no shop."""

    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(60))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    __table_args__ = (_one_of("role", Role),)

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    # Optional because customers may register with only a phone number (see Customer.phone,
    # the mandatory field for them). A plain unique index already allows any number of NULLs
    # in Postgres and SQLite, so this still rejects two accounts sharing one real email.
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
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
    shop: Mapped[Shop] = relationship()

    @property
    def shop_name(self) -> str:
        return self.shop.name

    @property
    def address(self) -> str | None:
        # None for staff; a customer's own address once they've raised their first complaint.
        return self.customer.address if self.customer else None


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    address: Mapped[str | None] = mapped_column(Text)
    # Mandatory and unique: a customer's email is optional, so phone is both their required
    # contact number and the identifier they can log in with when they have no email.
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    user: Mapped[User] = relationship(back_populates="customer")
    equipment: Mapped[list["Equipment"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def name(self) -> str:
        # So CustomerSummary (and anything else) can read .name without reaching into .user
        # itself; eager-load User when querying if this is used on more than a handful of rows.
        return self.user.name


class Technician(Base):
    __tablename__ = "technicians"
    __table_args__ = (_one_of("availability", Availability),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    skill_area: Mapped[str | None] = mapped_column(String(100))
    availability: Mapped[str] = mapped_column(String(20), default=Availability.AVAILABLE)

    user: Mapped[User] = relationship(back_populates="technician")

    @property
    def name(self) -> str:
        return self.user.name


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

    customer: Mapped[Customer] = relationship()
    equipment: Mapped["Equipment | None"] = relationship()
    technician: Mapped["Technician | None"] = relationship()
    category: Mapped["ComplaintCategory | None"] = relationship()


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
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), index=True)
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


class VoiceNote(Base):
    """A technician's spoken account of a job, recorded on their phone and transcribed on the
    server — see app.routes.voice_notes. The audio stays on disk (Settings.media_dir) so a wrong
    transcript can be checked against what was actually said."""

    __tablename__ = "voice_notes"
    __table_args__ = (_one_of("status", VoiceNoteStatus),)

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_requests.id", ondelete="CASCADE"), index=True)
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # Generated by the phone when recording starts. A retried upload (weak signal, app reopened)
    # sends the same id, so it's stored once however many times it arrives.
    client_id: Mapped[str] = mapped_column(String(64), unique=True)
    # Relative to Settings.media_dir.
    audio_path: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default=VoiceNoteStatus.PENDING)
    transcript: Mapped[str | None] = mapped_column(Text)
    # Which engine and model produced the transcript, e.g. "local:vasista22/whisper-tamil-small".
    engine: Mapped[str | None] = mapped_column(String(150))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    transcribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


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
