"""
Pytest configuration and fixtures
"""
import pytest
import os
import tempfile
from app import db
from app.models import Claim


@pytest.fixture
def app():
    """Create application for testing"""
    from flask import Flask

    # create temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # create Flask app with test configuration FIRST
    app = Flask(__name__,
                template_folder='app/templates',
                static_folder='../frontend/static')

    # configure BEFORE initializing db, otherwise db mixture happens
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })

    # Initialize db
    db.init_app(app)

    # IMPORTANT: Register all blueprints!, otherwise routes fail
    from app.routes import home, auth, claims, instructor
    app.register_blueprint(home.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(claims.bp)
    app.register_blueprint(instructor.bp)

    # tables in the temp database
    with app.app_context():
        db.create_all()

    yield app

    # Cleanup: close and remove temp database
    with app.app_context():
        db.session.remove()
        db.drop_all()

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

        claim_id = claim.id

    return claim_id