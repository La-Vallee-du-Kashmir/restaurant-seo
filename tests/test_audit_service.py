import pytest
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import (
    Restaurant,
    Location,
    Audit,
    AuditStatus,
    AuditFinding,
    FindingSeverity,
)
from app.services.analyzers import AuditFixture
from app.services.audit_service import AuditService


class TestAuditService:
    """Test deterministic audit engine."""

    @pytest.fixture
    async def setup_audit(self, test_session: AsyncSession):
        """Create restaurant, location, and audit for testing."""
        restaurant = Restaurant(name="Test Restaurant")
        location = Location(
            restaurant=restaurant,
            name="Main Location",
            url="https://example.com",
        )
        audit = Audit(
            restaurant=restaurant,
            status=AuditStatus.PENDING,
        )

        test_session.add(restaurant)
        test_session.add(location)
        test_session.add(audit)
        await test_session.commit()

        await test_session.refresh(audit)
        return audit

    @pytest.mark.asyncio
    async def test_audit_state_transitions(
        self,
        test_session: AsyncSession,
        setup_audit: Audit,
    ):
        """Test PENDING → RUNNING → COMPLETED transitions."""
        service = AuditService()
        fixture = AuditFixture(
            title="Test Page",
            meta_description="Test description",
            h1_count=1,
            performance_score=85,
            mobile_friendly=True,
        )

        result = await service.run_audit(setup_audit.id, test_session, fixture)

        assert result.status == AuditStatus.COMPLETED
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_audit_failure_handling(
        self,
        test_session: AsyncSession,
        setup_audit: Audit,
    ):
        """Test RUNNING → FAILED on exception."""
        service = AuditService()
        fixture = AuditFixture(
            title="Test Page",
            meta_description="Test description",
            h1_count=1,
            performance_score=85,
            mobile_friendly=True,
        )

        # Manually set to RUNNING to trigger error
        setup_audit.status = AuditStatus.RUNNING
        await test_session.commit()

        with pytest.raises(ValueError):
            await service.run_audit(setup_audit.id, test_session, fixture)

        # Verify state transitioned to FAILED
        stmt = select(Audit).where(Audit.id == setup_audit.id)
        result = await test_session.execute(stmt)
        audit = result.scalar_one()

        assert audit.status == AuditStatus.FAILED
        assert audit.error_message is not None

    @pytest.mark.asyncio
    async def test_deterministic_findings_good_page(
        self,
        test_session: AsyncSession,
        setup_audit: Audit,
    ):
        """Test that good page produces no findings."""
        service = AuditService()
        fixture = AuditFixture(
            title="Good Page Title for SEO",
            meta_description="This is a good meta description with proper length",
            h1_count=1,
            performance_score=90,
            mobile_friendly=True,
        )

        await service.run_audit(setup_audit.id, test_session, fixture)

        stmt = select(AuditFinding).where(AuditFinding.audit_id == setup_audit.id)
        result = await test_session.execute(stmt)
        findings = result.scalars().all()

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_deterministic_findings_bad_page(
        self,
        test_session: AsyncSession,
        setup_audit: Audit,
    ):
        """Test that bad page produces expected findings."""
        service = AuditService()
        fixture = AuditFixture(
            title=None,  # Missing title
            meta_description=None,  # Missing meta description
            h1_count=0,  # Missing H1
            performance_score=40,  # Poor performance
            mobile_friendly=False,  # Not mobile friendly
        )

        await service.run_audit(setup_audit.id, test_session, fixture)

        stmt = select(AuditFinding).where(AuditFinding.audit_id == setup_audit.id)
        result = await test_session.execute(stmt)
        findings = result.scalars().all()

        # Expect: missing_title (CRITICAL), missing_meta_description (HIGH),
        # missing_h1 (HIGH), poor_performance (CRITICAL), not_mobile_friendly (HIGH)
        assert len(findings) == 5

        severities = {f.severity for f in findings}
        assert FindingSeverity.CRITICAL in severities
        assert FindingSeverity.HIGH in severities

    @pytest.mark.asyncio
    async def test_deterministic_fixture_produces_same_findings(
        self,
        test_session: AsyncSession,
        setup_audit: Audit,
    ):
        """Test that same fixture always produces same findings."""
        service = AuditService()
        fixture = AuditFixture(
            title="Short",  # Too short
            meta_description="Meta",  # Too short
            h1_count=2,  # Multiple H1s
            performance_score=60,  # Moderate performance
            mobile_friendly=True,
        )

        # Run first time
        await service.run_audit(setup_audit.id, test_session, fixture)

        stmt = select(AuditFinding).where(AuditFinding.audit_id == setup_audit.id)
        result = await test_session.execute(stmt)
        findings_1 = sorted(
            result.scalars().all(),
            key=lambda f: f.type,
        )

        # Create new audit and run again with same fixture
        restaurant_stmt = select(Restaurant).limit(1)
        restaurant_result = await test_session.execute(restaurant_stmt)
        restaurant = restaurant_result.scalar_one()

        audit_2 = Audit(
            restaurant=restaurant,
            status=AuditStatus.PENDING,
        )
        test_session.add(audit_2)
        await test_session.commit()

        await service.run_audit(audit_2.id, test_session, fixture)

        stmt = select(AuditFinding).where(AuditFinding.audit_id == audit_2.id)
        result = await test_session.execute(stmt)
        findings_2 = sorted(
            result.scalars().all(),
            key=lambda f: f.type,
        )

        # Same fixture should produce same findings
        assert len(findings_1) == len(findings_2)
        for f1, f2 in zip(findings_1, findings_2):
            assert f1.type == f2.type
            assert f1.severity == f2.severity

    @pytest.mark.asyncio
    async def test_findings_persisted_in_database(
        self,
        test_session: AsyncSession,
        setup_audit: Audit,
    ):
        """Test that findings are actually persisted to database."""
        service = AuditService()
        fixture = AuditFixture(
            title=None,
            meta_description="Adequate description for testing",
            h1_count=1,
            performance_score=85,
            mobile_friendly=True,
        )

        await service.run_audit(setup_audit.id, test_session, fixture)

        # Verify in database
        stmt = (
            select(Audit)
            .where(Audit.id == setup_audit.id)
        )
        result = await test_session.execute(stmt)
        persisted_audit = result.scalar_one()

        assert persisted_audit.status == AuditStatus.COMPLETED

        findings_stmt = select(AuditFinding).where(
            AuditFinding.audit_id == setup_audit.id
        )
        findings_result = await test_session.execute(findings_stmt)
        findings = findings_result.scalars().all()

        assert len(findings) == 1
        assert findings[0].type == "missing_title"
        assert findings[0].severity == FindingSeverity.CRITICAL
