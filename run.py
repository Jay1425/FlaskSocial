from app import create_app, db, socketio
import os

app = create_app()

if __name__ == '__main__':
    # Create database tables for development
    with app.app_context():
        db.create_all()
    
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