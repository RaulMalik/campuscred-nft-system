"""
Pytest configuration and fixtures
"""
import pytest
import os
import tempfile
from app import create_app, db
from app.models import Claim


@pytest.fixture
def app():
    """Create application for testing"""
    # temporary database
    db_fd, db_path = tempfile.mkstemp()

    # app with test config
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
    })

    # create tables
    with app.app_context():
        db.create_all()

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_claim(app):
    """Create a sample claim for testing"""
    with app.app_context():
        claim = Claim(
            student_name='Test Student',
            student_email='test@student.dtu.dk',
            credential_type='micro-credential',
            course_code='02369',
            description='Test claim for unit testing',
            status='pending'
        )
        db.session.add(claim)
        db.session.commit()

        # return ID so tests can use it
        claim_id = claim.id

    return claim_id