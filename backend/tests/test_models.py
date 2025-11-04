"""
Tests for database models
"""
import pytest
from app import db
from app.models import Claim
from datetime import datetime


class TestClaimModel:
    """Test Claim model"""

    def test_create_claim(self, app):
        """Test creating a basic claim"""
        with app.app_context():
            claim = Claim(
                student_name='John Doe',
                student_email='john@dtu.dk',
                credential_type='course-completion',
                course_code='02102',
                description='Intro to Programming',
                status='pending'
            )
            db.session.add(claim)
            db.session.commit()

            # Verify claim was created
            assert claim.id is not None
            assert claim.student_name == 'John Doe'
            assert claim.status == 'pending'
            assert claim.created_at is not None

    def test_claim_defaults(self, app):
        """Test default values"""
        with app.app_context():
            claim = Claim(
                student_name='Jane Doe',
                student_email='jane@dtu.dk',
                credential_type='micro-credential',
                course_code='02369'
            )
            db.session.add(claim)
            db.session.commit()

            # Check defaults
            assert claim.status == 'pending'
            assert claim.token_id is None
            assert claim.approved_at is None

    def test_claim_repr(self, app):
        """Test string representation"""
        with app.app_context():
            claim = Claim(
                student_name='Test',
                student_email='test@dtu.dk',
                credential_type='micro-credential',
                course_code='02369',
                status='pending'
            )
            db.session.add(claim)
            db.session.commit()

            assert '02369' in repr(claim)
            assert 'pending' in repr(claim)

    def test_compute_file_hash(self, app, tmp_path):
        """Test file hash computation"""
        # Create a temporary test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        # Compute hash
        hash_result = Claim.compute_file_hash(str(test_file))

        # Verify it's a valid SHA-256 hash (64 hex characters)
        assert len(hash_result) == 64
        assert hash_result.isalnum()

        # Same file should produce same hash
        hash_result2 = Claim.compute_file_hash(str(test_file))
        assert hash_result == hash_result2

    def test_claim_status_workflow(self, app):
        """Test claim status changes"""
        with app.app_context():
            claim = Claim(
                student_name='Test',
                student_email='test@dtu.dk',
                credential_type='micro-credential',
                course_code='02369',
                status='pending'
            )
            db.session.add(claim)
            db.session.commit()

            # Approve claim
            claim.status = 'approved'
            claim.approved_at = datetime.utcnow()
            db.session.commit()

            assert claim.status == 'approved'
            assert claim.approved_at is not None