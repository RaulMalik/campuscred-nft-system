from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize extensions
db = SQLAlchemy()


def create_app():
    """Application factory function"""

    # Get the path to frontend/static
    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'static')

    # Create Flask app
    app = Flask(__name__,
                static_folder=static_folder,
                static_url_path='/static')

    # Load configuration
    from .config import Config
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints (ORDER MATTERS!)
    from .routes import home, auth, claims, instructor, verify
    app.register_blueprint(home.bp)  # This handles /
    app.register_blueprint(auth.bp)  # This handles /auth/*
    app.register_blueprint(claims.bp)   # Our student claim route
    app.register_blueprint(instructor.bp)
    app.register_blueprint(verify.bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app