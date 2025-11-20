#!/usr/bin/env python3
"""
Database initialization script for POP application.

This script initializes the database with default roles and admin user.
Run this once when setting up the application for the first time.

Usage:
    python init_db.py
"""

from app import create_app, db
from app.utils.init_db import initialize_database, check_initialization_needed

def main():
    """Main initialization function."""
    # Create application context
    app = create_app()
    
    with app.app_context():
        # Create all database tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created\n")
        
        # Check if initialization is needed
        if check_initialization_needed():
            print("Database is empty. Running initialization...\n")
            initialize_database()
        else:
            print("Database already initialized. Running initialization again to ensure defaults exist...\n")
            initialize_database()
        
        print("\n✅ Database is ready!")
        print("\nYou can now run the application with:")
        print("  flask run")
        print("\nDefault admin credentials:")
        print("  Username: admin (or as configured in .env)")
        print("  Password: check ADMIN_PASSWORD in .env")

if __name__ == '__main__':
    main()
