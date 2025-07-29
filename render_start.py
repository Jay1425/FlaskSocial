#!/usr/bin/env python3
"""
Production startup script for Render.com deployment.
This script handles database migrations and starts the application with Gunicorn.
"""

import os
import subprocess
import sys
from app import create_app, db

def run_migrations():
    """Run database migrations if needed."""
    try:
        # Initialize migration repository if it doesn't exist
        if not os.path.exists('migrations'):
            print("🔧 Initializing database migrations...")
            subprocess.run(['flask', 'db', 'init'], check=True)
        
        # Create migration if needed
        print("🔧 Creating migration...")
        result = subprocess.run(['flask', 'db', 'migrate', '-m', 'Auto migration'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration created successfully")
        else:
            print("ℹ️ No new migrations needed")
        
        # Apply migrations
        print("🔧 Applying database migrations...")
        subprocess.run(['flask', 'db', 'upgrade'], check=True)
        print("✅ Database migrations completed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration error: {e}")
        # Fallback: create tables directly
        print("🔧 Fallback: Creating tables directly...")
        app = create_app()
        with app.app_context():
            db.create_all()
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        sys.exit(1)

def main():
    """Main function to start the application."""
    print("🚀 Starting Commune Flask App for Render.com")
    print("=" * 50)
    
    # Set Flask app environment variable
    os.environ['FLASK_APP'] = 'run.py'
    
    # Check if we're in production
    if os.environ.get('DATABASE_URL'):
        print("✅ Production environment detected")
        print("✅ Database URL configured")
        
        # Run migrations in production
        run_migrations()
    else:
        print("ℹ️ Development environment")
        # Create tables for development
        app = create_app()
        with app.app_context():
            db.create_all()
    
    print("=" * 50)
    print("🎉 Application ready!")
    
    # Start the application
    # Note: On Render.com, this script is used for setup
    # The actual server is started by Gunicorn via render.yaml or build command

if __name__ == '__main__':
    main()
