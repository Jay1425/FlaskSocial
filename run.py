from app import create_app, db, socketio
import os

app = create_app()

# Fix for SQLAlchemy threading issues with eventlet
import eventlet
eventlet.monkey_patch()

if __name__ == '__main__':
    # Create database tables for development
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"⚠️  Database initialization warning: {e}")
    
    # Configuration for different environments
    port = int(os.environ.get('PORT', 5000))
    debug = not os.environ.get('RENDER')  # Disable debug in production
    
    if os.environ.get('RENDER'):
        # Production on Render.com
        print("🚀 Starting production server on Render.com")
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
    else:
        # Development
        print("🔧 Starting development server")
        socketio.run(app, host='127.0.0.1', port=port, debug=debug)