from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AuditFixtureRequest(BaseModel):
    """Request model for audit fixture input."""

    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1_count: int = Field(default=0, ge=0)
    performance_score: int = Field(default=75, ge=0, le=100)
    mobile_friendly: bool = True


class AuditCreate(BaseModel):
    """Request model for creating an audit."""

    restaurant_id: int
    project_id: Optional[int] = None
    fixture: AuditFixtureRequest


class AuditResponse(BaseModel):
    """Response model for an audit."""

    id: int
    restaurant_id: Optional[int]
    project_id: Optional[int]
    status: str
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditFindingResponse(BaseModel):
    """Response model for an audit finding."""

    id: int
    audit_id: int
    severity: str
    type: str
    page_url: str

    model_config = ConfigDict(from_attributes=True)
