import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app
from app.schemas.audit import AuditFixtureRequest


@pytest.fixture
def override_get_db(test_session: AsyncSession):
    """Override get_db dependency with test session."""

    async def _override_get_db():
        yield test_session

    return _override_get_db


@pytest.fixture
def client(override_get_db):
    """FastAPI test client with overridden database dependency."""
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestAPI:
    """Integration tests for restaurant and audit API."""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_create_restaurant(self, client: TestClient):
        """Test POST /api/v1/restaurants."""
        response = client.post(
            "/api/v1/restaurants",
            json={"name": "Test Restaurant"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Restaurant"
        assert "id" in data

    def test_get_restaurant(self, client: TestClient):
        """Test GET /api/v1/restaurants/{restaurant_id}."""
        # Create a restaurant
        create_resp = client.post(
            "/api/v1/restaurants",
            json={"name": "Test Restaurant"},
        )
        restaurant_id = create_resp.json()["id"]

        # Retrieve it
        get_resp = client.get(f"/api/v1/restaurants/{restaurant_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == restaurant_id
        assert data["name"] == "Test Restaurant"

    def test_get_nonexistent_restaurant(self, client: TestClient):
        """Test GET /api/v1/restaurants/{restaurant_id} with invalid ID."""
        response = client.get("/api/v1/restaurants/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_audit_success(self, client: TestClient):
        """Test POST /api/v1/audits with valid data."""
        # Create restaurant
        restaurant_resp = client.post(
            "/api/v1/restaurants",
            json={"name": "Test Restaurant"},
        )
        restaurant_id = restaurant_resp.json()["id"]

        # Create audit
        audit_resp = client.post(
            "/api/v1/audits",
            json={
                "restaurant_id": restaurant_id,
                "project_id": None,
                "fixture": {
                    "title": "Good Page Title",
                    "meta_description": "This is a good meta description",
                    "h1_count": 1,
                    "performance_score": 90,
                    "mobile_friendly": True,
                },
            },
        )
        assert audit_resp.status_code == 201
        data = audit_resp.json()
        assert data["status"] == "completed"
        assert data["restaurant_id"] == restaurant_id
        assert data["error_message"] is None

    def test_create_audit_nonexistent_restaurant(
        self,
        client: TestClient,
    ):
        """Test POST /api/v1/audits with nonexistent restaurant."""
        response = client.post(
            "/api/v1/audits",
            json={
                "restaurant_id": 9999,
                "project_id": None,
                "fixture": {
                    "title": "Test",
                    "meta_description": "Test",
                    "h1_count": 1,
                    "performance_score": 75,
                    "mobile_friendly": True,
                },
            },
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_audit_invalid_payload(self, client: TestClient):
        """Test POST /api/v1/audits with invalid payload."""
        response = client.post(
            "/api/v1/audits",
            json={
                "restaurant_id": "not_an_int",
            },
        )
        assert response.status_code == 422

    def test_get_audit(self, client: TestClient):
        """Test GET /api/v1/audits/{audit_id}."""
        # Create restaurant and audit
        restaurant_resp = client.post(
            "/api/v1/restaurants",
            json={"name": "Test Restaurant"},
        )
        restaurant_id = restaurant_resp.json()["id"]

        audit_resp = client.post(
            "/api/v1/audits",
            json={
                "restaurant_id": restaurant_id,
                "fixture": {
                    "title": "Test",
                    "meta_description": "Test description",
                    "h1_count": 1,
                    "performance_score": 75,
                    "mobile_friendly": True,
                },
            },
        )
        audit_id = audit_resp.json()["id"]

        # Retrieve audit
        get_resp = client.get(f"/api/v1/audits/{audit_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == audit_id
        assert data["status"] == "completed"

    def test_get_nonexistent_audit(self, client: TestClient):
        """Test GET /api/v1/audits/{audit_id} with invalid ID."""
        response = client.get("/api/v1/audits/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_audit_findings(self, client: TestClient):
        """Test GET /api/v1/audits/{audit_id}/findings."""
        # Create restaurant and audit with bad fixture
        restaurant_resp = client.post(
            "/api/v1/restaurants",
            json={"name": "Test Restaurant"},
        )
        restaurant_id = restaurant_resp.json()["id"]

        audit_resp = client.post(
            "/api/v1/audits",
            json={
                "restaurant_id": restaurant_id,
                "fixture": {
                    "title": None,  # Missing title
                    "meta_description": None,  # Missing description
                    "h1_count": 0,  # Missing H1
                    "performance_score": 40,  # Poor performance
                    "mobile_friendly": False,  # Not mobile friendly
                },
            },
        )
        audit_id = audit_resp.json()["id"]

        # Retrieve findings
        findings_resp = client.get(f"/api/v1/audits/{audit_id}/findings")
        assert findings_resp.status_code == 200
        findings = findings_resp.json()
        assert len(findings) == 5  # 5 findings from bad fixture
        assert all("id" in f and "severity" in f for f in findings)

    def test_get_findings_nonexistent_audit(self, client: TestClient):
        """Test GET /api/v1/audits/{audit_id}/findings with invalid ID."""
        response = client.get("/api/v1/audits/9999/findings")
        assert response.status_code == 404

    def test_findings_match_database(self, client: TestClient, test_session):
        """Test that returned findings match persisted database records."""
        # Create restaurant and audit
        restaurant_resp = client.post(
            "/api/v1/restaurants",
            json={"name": "Test Restaurant"},
        )
        restaurant_id = restaurant_resp.json()["id"]

        audit_resp = client.post(
            "/api/v1/audits",
            json={
                "restaurant_id": restaurant_id,
                "fixture": {
                    "title": "Short",  # Too short
                    "meta_description": None,
                    "h1_count": 1,
                    "performance_score": 75,
                    "mobile_friendly": True,
                },
            },
        )
        audit_id = audit_resp.json()["id"]

        # Get findings via API
        findings_resp = client.get(f"/api/v1/audits/{audit_id}/findings")
        api_findings = findings_resp.json()

        # Verify findings match database
        assert len(api_findings) == 2  # title_too_short, missing_meta_description
        types = {f["type"] for f in api_findings}
        assert "title_too_short" in types
        assert "missing_meta_description" in types

    def test_audit_deterministic(self, client: TestClient):
        """Test that same fixture produces same findings."""
        # Create restaurant
        restaurant_resp = client.post(
            "/api/v1/restaurants",
            json={"name": "Test Restaurant"},
        )
        restaurant_id = restaurant_resp.json()["id"]

        fixture = {
            "title": "Test Title",
            "meta_description": "Test description for testing",
            "h1_count": 1,
            "performance_score": 85,
            "mobile_friendly": True,
        }

        # Create first audit
        audit_resp_1 = client.post(
            "/api/v1/audits",
            json={
                "restaurant_id": restaurant_id,
                "fixture": fixture,
            },
        )
        audit_id_1 = audit_resp_1.json()["id"]
        findings_1_resp = client.get(f"/api/v1/audits/{audit_id_1}/findings")
        findings_1 = sorted(
            findings_1_resp.json(),
            key=lambda f: f["type"],
        )

        # Create second audit with same fixture
        audit_resp_2 = client.post(
            "/api/v1/audits",
            json={
                "restaurant_id": restaurant_id,
                "fixture": fixture,
            },
        )
        audit_id_2 = audit_resp_2.json()["id"]
        findings_2_resp = client.get(f"/api/v1/audits/{audit_id_2}/findings")
        findings_2 = sorted(
            findings_2_resp.json(),
            key=lambda f: f["type"],
        )

        # Same fixture should produce same findings
        assert len(findings_1) == len(findings_2)
        for f1, f2 in zip(findings_1, findings_2):
            assert f1["type"] == f2["type"]
            assert f1["severity"] == f2["severity"]
