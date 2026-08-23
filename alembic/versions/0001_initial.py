"""Initial schema creation.

Revision ID: 0001
Revises: None
Create Date: 2026-08-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    audit_status_enum = postgresql.ENUM(
        "pending", "running", "completed", "failed",
        name="auditstatus",
        create_type=True,
    )
    audit_status_enum.create(op.get_bind(), checkfirst=True)

    severity_enum = postgresql.ENUM(
        "info", "low", "medium", "high", "critical",
        name="findingseverity",
        create_type=True,
    )
    severity_enum.create(op.get_bind(), checkfirst=True)

    # Create restaurants table
    op.create_table(
        "restaurants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_restaurants_name", "restaurants", ["name"], unique=False)

    # Create locations table
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_locations_restaurant_id", "locations", ["restaurant_id"])
    op.create_index("ix_locations_url", "locations", ["url"])
    op.create_index(
        "ix_location_restaurant_url",
        "locations",
        ["restaurant_id", "url"],
    )

    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_restaurant_id", "projects", ["restaurant_id"])
    op.create_index("ix_projects_name", "projects", ["name"])

    # Create audits table
    op.create_table(
        "audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="auditstatus"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audits_restaurant_id", "audits", ["restaurant_id"])
    op.create_index("ix_audits_project_id", "audits", ["project_id"])
    op.create_index("ix_audits_status", "audits", ["status"])
    op.create_index(
        "ix_audit_restaurant_status",
        "audits",
        ["restaurant_id", "status"],
    )
    op.create_index(
        "ix_audit_project_status",
        "audits",
        ["project_id", "status"],
    )

    # Create audit_findings table
    op.create_table(
        "audit_findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column(
            "severity",
            sa.Enum("info", "low", "medium", "high", "critical", name="findingseverity"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("page_url", sa.String(length=2048), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_findings_audit_id", "audit_findings", ["audit_id"])
    op.create_index("ix_audit_findings_severity", "audit_findings", ["severity"])
    op.create_index("ix_audit_findings_type", "audit_findings", ["type"])
    op.create_index(
        "ix_finding_audit_severity",
        "audit_findings",
        ["audit_id", "severity"],
    )


def downgrade() -> None:
    # Drop audit_findings table
    op.drop_table("audit_findings")

    # Drop audits table
    op.drop_table("audits")

    # Drop projects table
    op.drop_table("projects")

    # Drop locations table
    op.drop_table("locations")

    # Drop restaurants table
    op.drop_table("restaurants")

    # Drop enum types
    sa.Enum("pending", "running", "completed", "failed", name="auditstatus").drop(
        op.get_bind(),
        checkfirst=True,
    )
    sa.Enum(
        "info", "low", "medium", "high", "critical",
        name="findingseverity",
    ).drop(
        op.get_bind(),
        checkfirst=True,
    )
