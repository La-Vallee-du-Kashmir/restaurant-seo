from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Audit, AuditFinding, Restaurant
from app.db.session import get_db
from app.schemas.audit import (
    AuditCreate,
    AuditResponse,
    AuditFindingResponse,
    AuditFixtureRequest,
)
from app.services.analyzers import AuditFixture
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1", tags=["audits"])


@router.post(
    "/audits",
    response_model=AuditResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_audit(
    req: AuditCreate,
    session: AsyncSession = Depends(get_db),
) -> AuditResponse:
    """Create and run an audit.

    Verifies restaurant exists before creating the audit.
    Converts AuditFixtureRequest to internal AuditFixture.
    Runs the audit immediately and returns final state.
    """
    # Verify restaurant exists
    stmt = select(Restaurant).where(Restaurant.id == req.restaurant_id)
    result = await session.execute(stmt)
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    # Create audit
    audit = Audit(
        restaurant_id=req.restaurant_id,
        project_id=req.project_id,
    )
    session.add(audit)
    await session.commit()
    await session.refresh(audit)

    # Convert request fixture to internal AuditFixture
    fixture = AuditFixture(
        title=req.fixture.title,
        meta_description=req.fixture.meta_description,
        h1_count=req.fixture.h1_count,
        performance_score=req.fixture.performance_score,
        mobile_friendly=req.fixture.mobile_friendly,
    )

    # Run audit
    try:
        service = AuditService()
        audit = await service.run_audit(audit.id, session, fixture)
    except Exception as e:
        # Service has already persisted FAILED state
        # Refresh to get updated state and error_message
        await session.refresh(audit)

    return AuditResponse.model_validate(audit)


@router.get(
    "/audits/{audit_id}",
    response_model=AuditResponse,
)
async def get_audit(
    audit_id: int,
    session: AsyncSession = Depends(get_db),
) -> AuditResponse:
    """Retrieve an audit by ID."""
    stmt = select(Audit).where(Audit.id == audit_id)
    result = await session.execute(stmt)
    audit = result.scalar_one_or_none()

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit not found",
        )

    return AuditResponse.model_validate(audit)


@router.get(
    "/audits/{audit_id}/findings",
    response_model=list[AuditFindingResponse],
)
async def get_audit_findings(
    audit_id: int,
    session: AsyncSession = Depends(get_db),
) -> list[AuditFindingResponse]:
    """Retrieve findings for an audit."""
    # Verify audit exists
    audit_stmt = select(Audit).where(Audit.id == audit_id)
    audit_result = await session.execute(audit_stmt)
    audit = audit_result.scalar_one_or_none()

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit not found",
        )

    # Retrieve findings
    findings_stmt = select(AuditFinding).where(
        AuditFinding.audit_id == audit_id
    )
    findings_result = await session.execute(findings_stmt)
    findings = findings_result.scalars().all()

    return [
        AuditFindingResponse.model_validate(finding)
        for finding in findings
    ]
