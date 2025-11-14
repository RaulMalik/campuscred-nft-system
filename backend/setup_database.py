"""
Database Setup Script
Run this after cloning the repository to create your local database
"""

from app import create_app, db
from app.models import Claim
from sqlalchemy import inspect


def setup_database():
    """Create database tables from models.py"""
    app = create_app()

    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        # Verify tables were created
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Database created successfully!")
        print(f"Tables: {', '.join(tables)}")

        print("\nSetup complete! You can now run: python run.py")


if __name__ == '__main__':
    setup_database()