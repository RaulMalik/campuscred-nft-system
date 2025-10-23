from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize extensions
db = SQLAlchemy()


def create_app():
    """Application factory function"""

    # Get the path to frontend/static
    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'static')

    # Create Flask app with custom static folder
    app = Flask(__name__,
                static_folder=static_folder,
                static_url_path='/static')

    # Load configuration
    from .config import Config
    app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)

    # Register blueprints (routes)
    from .routes import auth
    app.register_blueprint(auth.bp)

    # Add root route
    @app.route('/')
    def index():
        return jsonify({
            'project': 'CampusCred',
            'description': 'NFT-based Academic Credential System',
            'version': '0.1.0',
            'status': 'running',
            'endpoints': {
                'home': '/',
                'auth': '/auth/',
                'test': '/auth/test'
            }
        })

    # Create database tables
    with app.app_context():
        db.create_all()

    return app