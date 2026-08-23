from dataclasses import dataclass
from typing import Optional

from app.db.models import AuditFinding, FindingSeverity


@dataclass(frozen=True)
class AuditFixture:
    """Deterministic audit input fixture."""

    title: Optional[str]
    meta_description: Optional[str]
    h1_count: int
    performance_score: int
    mobile_friendly: bool


class TitleAnalyzer:
    """Analyze page title presence and length."""

    async def analyze(self, fixture: AuditFixture) -> list[AuditFinding]:
        findings = []

        if fixture.title is None:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.CRITICAL,
                    type="missing_title",
                    page_url="",
                )
            )
        elif len(fixture.title) < 30:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.HIGH,
                    type="title_too_short",
                    page_url="",
                )
            )
        elif len(fixture.title) > 60:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.MEDIUM,
                    type="title_too_long",
                    page_url="",
                )
            )

        return findings


class MetaDescriptionAnalyzer:
    """Analyze meta description presence and length."""

    async def analyze(self, fixture: AuditFixture) -> list[AuditFinding]:
        findings = []

        if fixture.meta_description is None:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.HIGH,
                    type="missing_meta_description",
                    page_url="",
                )
            )
        elif len(fixture.meta_description) < 50:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.MEDIUM,
                    type="meta_description_too_short",
                    page_url="",
                )
            )
        elif len(fixture.meta_description) > 160:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.MEDIUM,
                    type="meta_description_too_long",
                    page_url="",
                )
            )

        return findings


class HeadingAnalyzer:
    """Analyze heading structure."""

    async def analyze(self, fixture: AuditFixture) -> list[AuditFinding]:
        findings = []

        if fixture.h1_count == 0:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.HIGH,
                    type="missing_h1",
                    page_url="",
                )
            )
        elif fixture.h1_count > 1:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.MEDIUM,
                    type="multiple_h1",
                    page_url="",
                )
            )

        return findings


class PerformanceAnalyzer:
    """Analyze page performance score."""

    async def analyze(self, fixture: AuditFixture) -> list[AuditFinding]:
        findings = []

        if fixture.performance_score < 50:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.CRITICAL,
                    type="poor_performance",
                    page_url="",
                )
            )
        elif fixture.performance_score < 75:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.HIGH,
                    type="moderate_performance",
                    page_url="",
                )
            )

        return findings


class MobileAnalyzer:
    """Analyze mobile friendliness."""

    async def analyze(self, fixture: AuditFixture) -> list[AuditFinding]:
        findings = []

        if not fixture.mobile_friendly:
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.HIGH,
                    type="not_mobile_friendly",
                    page_url="",
                )
            )

        return findings
