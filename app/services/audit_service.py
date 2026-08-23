from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.db.models import Audit, AuditStatus, Location
from app.services.analyzers import (
    AuditFixture,
    TitleAnalyzer,
    MetaDescriptionAnalyzer,
    HeadingAnalyzer,
    PerformanceAnalyzer,
    MobileAnalyzer,
)


class AuditService:
    """Deterministic SEO audit execution service."""

    def __init__(self):
        self.analyzers = [
            TitleAnalyzer(),
            MetaDescriptionAnalyzer(),
            HeadingAnalyzer(),
            PerformanceAnalyzer(),
            MobileAnalyzer(),
        ]

    async def run_audit(
        self,
        audit_id: int,
        session: AsyncSession,
        fixture: AuditFixture,
    ) -> Audit:
        """Execute audit with explicit fixture input.

        Transitions: PENDING → RUNNING → COMPLETED
        On exception: RUNNING → FAILED with error_message.

        Args:
            audit_id: Audit database ID.
            session: AsyncSession for database operations.
            fixture: Deterministic audit input data.

        Returns:
            Updated Audit object.

        Raises:
            ValueError: If audit not found or in invalid state.
        """
        try:
            # Fetch audit with relationships
            stmt = (
                select(Audit)
                .where(Audit.id == audit_id)
                .options(selectinload(Audit.location))
            )
            result = await session.execute(stmt)
            audit = result.scalar_one_or_none()

            if not audit:
                raise ValueError(f"Audit {audit_id} not found")

            if audit.status != AuditStatus.PENDING:
                raise ValueError(
                    f"Audit {audit_id} is in {audit.status} state, expected PENDING"
                )

            # Transition to RUNNING
            audit.status = AuditStatus.RUNNING
            audit.started_at = datetime.now(timezone.utc)
            await session.flush()

            # Execute analyzers and collect findings
            all_findings = []
            for analyzer in self.analyzers:
                findings = await analyzer.analyze(fixture)
                all_findings.extend(findings)

            # Persist findings
            for finding in all_findings:
                finding.audit_id = audit.id
                session.add(finding)

            # Transition to COMPLETED
            audit.status = AuditStatus.COMPLETED
            audit.completed_at = datetime.now(timezone.utc)
            audit.error_message = None

            await session.commit()
            return audit

        except Exception as e:
            # Rollback to ensure no partial persistence
            await session.rollback()

            # Fetch audit again to update state
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            audit = result.scalar_one_or_none()

            if audit:
                audit.status = AuditStatus.FAILED
                audit.error_message = str(e)
                audit.completed_at = datetime.now(timezone.utc)
                await session.commit()

            raise
