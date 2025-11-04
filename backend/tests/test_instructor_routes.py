"""
Tests for instructor dashboard routes
"""
import pytest
from app import db
from app.models import Claim
import json


class TestInstructorDashboard:
    """Test instructor dashboard functionality"""

    def test_dashboard_loads(self, client):
        """Test that instructor dashboard loads"""
        response = client.get('/instructor/dashboard')
        assert response.status_code == 200
        assert b'Instructor Dashboard' in response.data
        assert b'Pending Claims' in response.data

    def test_dashboard_shows_statistics(self, client, sample_claim):
        """Test dashboard shows correct statistics"""
        response = client.get('/instructor/dashboard')

        assert b'Total Claims' in response.data
        assert b'Pending Approval' in response.data

    def test_get_claim_details(self, client, sample_claim):
        """Test fetching claim details"""
        response = client.get(f'/instructor/claim/{sample_claim}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_claim
        assert data['student_name'] == 'Test Student'
        assert data['course_code'] == '02369'

    def test_get_nonexistent_claim(self, client):
        """Test fetching non-existent claim returns 404"""
        response = client.get('/instructor/claim/99999')
        assert response.status_code == 404

    def test_approve_claim(self, client, app, sample_claim):
        """Test approving a claim"""
        response = client.post(f'/instructor/approve/{sample_claim}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify in database
        with app.app_context():
            claim = Claim.query.get(sample_claim)
            assert claim.status == 'approved'
            assert claim.approved_at is not None

    def test_approve_already_approved_claim(self, client, app, sample_claim):
        """Test approving an already approved claim fails"""
        # First approval
        client.post(f'/instructor/approve/{sample_claim}')

        # Try to approve again
        response = client.post(f'/instructor/approve/{sample_claim}')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_reject_claim(self, client, app, sample_claim):
        """Test rejecting a claim"""
        response = client.post(
            f'/instructor/reject/{sample_claim}',
            data=json.dumps({'reason': 'Invalid evidence'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify in database
        with app.app_context():
            claim = Claim.query.get(sample_claim)
            assert claim.status == 'denied'
            assert claim.instructor_notes == 'Invalid evidence'

    def test_reject_without_reason(self, client, app, sample_claim):
        """Test rejecting without reason uses default"""
        response = client.post(
            f'/instructor/reject/{sample_claim}',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 200

        with app.app_context():
            claim = Claim.query.get(sample_claim)
            assert claim.instructor_notes == 'No reason provided'