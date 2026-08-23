from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditStatus(str, Enum):
    """Audit execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingSeverity(str, Enum):
    """SEO finding severity level."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Restaurant(Base):
    """Restaurant entity."""

    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    locations: Mapped[list["Location"]] = relationship(
        "Location",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="restaurant",
        cascade="all, delete-orphan",
        foreign_keys="Project.restaurant_id",
    )
    audits: Mapped[list["Audit"]] = relationship(
        "Audit",
        back_populates="restaurant",
        cascade="all, delete-orphan",
        foreign_keys="Audit.restaurant_id",
    )


class Location(Base):
    """Restaurant location/profile."""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    restaurant: Mapped[Restaurant] = relationship(
        "Restaurant",
        back_populates="locations",
    )

    __table_args__ = (
        Index("ix_location_restaurant_url", "restaurant_id", "url"),
    )


class Project(Base):
    """SEO audit project."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int | None] = mapped_column(
        ForeignKey("restaurants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    restaurant: Mapped[Restaurant | None] = relationship(
        "Restaurant",
        back_populates="projects",
        foreign_keys=[restaurant_id],
    )
    audits: Mapped[list["Audit"]] = relationship(
        "Audit",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="Audit.project_id",
    )


class Audit(Base):
    """SEO audit execution."""

    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int | None] = mapped_column(
        ForeignKey("restaurants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[AuditStatus] = mapped_column(
        SQLEnum(AuditStatus),
        default=AuditStatus.PENDING,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    restaurant: Mapped[Restaurant | None] = relationship(
        "Restaurant",
        back_populates="audits",
        foreign_keys=[restaurant_id],
    )
    project: Mapped[Project | None] = relationship(
        "Project",
        back_populates="audits",
        foreign_keys=[project_id],
    )
    findings: Mapped[list["AuditFinding"]] = relationship(
        "AuditFinding",
        back_populates="audit",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_audit_restaurant_status", "restaurant_id", "status"),
        Index("ix_audit_project_status", "project_id", "status"),
    )


class AuditFinding(Base):
    """SEO finding from an audit."""

    __tablename__ = "audit_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        SQLEnum(FindingSeverity),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    page_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    audit: Mapped[Audit] = relationship(
        "Audit",
        back_populates="findings",
    )

    __table_args__ = (
        Index("ix_finding_audit_severity", "audit_id", "severity"),
    )
