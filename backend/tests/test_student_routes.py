"""
Tests for student portal routes
"""
import pytest
from app import db
from app.models import Claim
import io


class TestStudentPortal:
    """Test student portal functionality"""

    def test_portal_page_loads(self, client):
        """Test that student portal page loads"""
        response = client.get('/student/portal')
        assert response.status_code == 200
        assert b'Student Portal' in response.data
        assert b'Claim New Credential' in response.data

    def test_submit_claim_success(self, client, app):
        """Test successful claim submission"""
        response = client.post('/student/submit-claim', data={
            'student_name': 'Alice Johnson',
            'student_email': 'alice@student.dtu.dk',
            'credential_type': 'micro-credential',
            'course_code': '02369',
            'course_name': 'Software Processes',
            'description': 'Completed all assignments'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Claim submitted successfully' in response.data

        # Verify in database
        with app.app_context():
            claim = Claim.query.filter_by(student_email='alice@student.dtu.dk').first()
            assert claim is not None
            assert claim.course_code == '02369'
            assert claim.status == 'pending'

    def test_submit_claim_missing_fields(self, client):
        """Test submission with missing required fields"""
        response = client.post('/student/submit-claim', data={
            'student_name': 'Bob',
            # Missing email, type, course_code
        }, follow_redirects=True)

        assert b'required' in response.data.lower()

    def test_submit_claim_invalid_email(self, client):
        """Test submission with invalid email"""
        response = client.post('/student/submit-claim', data={
            'student_name': 'Charlie',
            'student_email': 'not-an-email',
            'credential_type': 'micro-credential',
            'course_code': '02369'
        }, follow_redirects=True)

        assert b'valid email' in response.data.lower()

    def test_submit_claim_with_file(self, client, app):
        """Test claim submission with file upload"""
        # Create fake file
        data = {
            'student_name': 'David',
            'student_email': 'david@student.dtu.dk',
            'credential_type': 'course-completion',
            'course_code': '02102',
            'evidence': (io.BytesIO(b"test file content"), 'test.pdf')
        }

        response = client.post('/student/submit-claim',
                               data=data,
                               content_type='multipart/form-data',
                               follow_redirects=True)

        assert response.status_code == 200

        # Verify file was saved
        with app.app_context():
            claim = Claim.query.filter_by(student_email='david@student.dtu.dk').first()
            assert claim.evidence_file_name == 'test.pdf'
            assert claim.evidence_file_hash is not None
            assert len(claim.evidence_file_hash) == 64

    def test_portal_shows_claims(self, client, sample_claim):
        """Test that portal displays submitted claims"""
        response = client.get('/student/portal')

        assert response.status_code == 200
        assert b'02369' in response.data
        assert b'pending' in response.data.lower()