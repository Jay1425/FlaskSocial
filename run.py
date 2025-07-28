from app import create_app, db, socketio

app = create_app()

if __name__ == '__main__':
    # With the new Message model, you might need to recreate your DB.
    # For a real app, you'd use migrations (e.g., Flask-Migrate).
    # For this project, deleting site.db and restarting is the simplest way.
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)