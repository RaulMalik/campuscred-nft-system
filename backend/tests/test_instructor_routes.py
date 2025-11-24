"""
Tests for instructor dashboard routes
"""

import json
import pytest

from app import db
from app.models import Claim
from app.routes.auth import INSTRUCTOR_WALLET


@pytest.fixture
def instructor_client(client):
    """
    Test client with an instructor wallet in the session.
    This matches the requirement in app.routes.auth.instructor_required.
    """
    with client.session_transaction() as sess:
        sess["wallet_address"] = INSTRUCTOR_WALLET.lower()
        sess["is_instructor"] = True
    return client


class TestInstructorDashboard:
    """Instructor dashboard functionality"""

    def test_dashboard_loads(self, instructor_client):
        """Dashboard should load for an authenticated instructor"""
        response = instructor_client.get("/instructor/dashboard")
        assert response.status_code == 200
        assert b"Instructor Dashboard" in response.data
        assert b"Pending Claims" in response.data

    def test_dashboard_shows_statistics(self, instructor_client, sample_claim):
        """Dashboard shows summary statistics"""
        response = instructor_client.get("/instructor/dashboard")
        assert response.status_code == 200
        assert b"Total Claims" in response.data
        assert b"Pending Approval" in response.data

    def test_get_claim_details(self, instructor_client, sample_claim):
        """Fetch claim details as JSON for modal"""
        response = instructor_client.get(f"/instructor/claim/{sample_claim}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["id"] == sample_claim
        assert data["student_name"] == "Test Student"
        assert data["course_code"] == "02369"

    def test_get_nonexistent_claim(self, instructor_client):
        """Fetching a non-existent claim returns 404"""
        response = instructor_client.get("/instructor/claim/99999")
        assert response.status_code == 404

    def test_approve_claim(self, instructor_client, app, sample_claim):
        """
        Approving a pending claim:
        - returns success=True
        - moves status from 'pending' -> 'approved'
        - sets approved_at
        """
        response = instructor_client.post(f"/instructor/approve/{sample_claim}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        # If no wallet on the claim, status should remain 'approved'
        assert data["status"] in ("approved", "minted")

        with app.app_context():
            claim = Claim.query.get(sample_claim)
            assert claim is not None
            assert claim.status in ("approved", "minted")
            assert claim.approved_at is not None

    def test_approve_already_approved_claim(self, instructor_client, app, sample_claim):
        """Approving an already processed claim returns 400 and success=False"""
        # First approval
        instructor_client.post(f"/instructor/approve/{sample_claim}")

        # Second approval should fail
        response = instructor_client.post(f"/instructor/approve/{sample_claim}")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data["success"] is False
        assert "already" in data["error"].lower()

    def test_reject_claim(self, instructor_client, app, sample_claim):
        """Rejecting a pending claim sets status to 'denied' and stores reason"""
        response = instructor_client.post(
            f"/instructor/reject/{sample_claim}",
            data=json.dumps({"reason": "Invalid evidence"}),
            content_type="application/json",
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True

        with app.app_context():
            claim = Claim.query.get(sample_claim)
            assert claim is not None
            assert claim.status == "denied"
            assert claim.instructor_notes == "Invalid evidence"

    def test_reject_without_reason_uses_default(self, instructor_client, app, sample_claim):
        """Rejecting without explicit reason uses the default text"""
        response = instructor_client.post(
            f"/instructor/reject/{sample_claim}",
            data=json.dumps({}),  # no reason field
            content_type="application/json",
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True

        with app.app_context():
            claim = Claim.query.get(sample_claim)
            assert claim is not None
            assert claim.status == "denied"
            assert claim.instructor_notes == "No reason provided"