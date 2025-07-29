import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, Blueprint, abort, current_app
from app import db, bcrypt, socketio
from app.forms import RegistrationForm, LoginForm, PostForm, UpdateAccountForm
from app.models import User, Post, Message
from flask_login import login_user, current_user, logout_user, login_required
from flask_socketio import send, emit, join_room, leave_room
from sqlalchemy import or_

main = Blueprint('main', __name__)
user_sids = {}
call_rooms = {}

# -------------------- ROUTES --------------------

@main.route("/")
@main.route("/home")
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('home.html', posts=posts)

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@main.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@main.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('main.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@main.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('main.home'))

# -------------------- CHAT ROUTES --------------------

@main.route("/chat")
@login_required
def chat():
    return render_template('chat.html', title='Chat')

# -------------------- SOCKET.IO HANDLERS --------------------

@socketio.on('message')
def handle_message(msg):
    print(f'Message received: {msg}')
    send(msg, broadcast=True)

@socketio.on('json')
def handle_json(json):
    print('Received json:', json)
    payload = {
        'message': json['message'],
        'username': getattr(current_user, 'username', 'Anonymous')
    }
    emit('message_response', payload, broadcast=True)

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        username = getattr(current_user, 'username', 'User')
        print(f'{username} connected.')
        emit('message_response', {'message': f'{username} has joined the chat.', 'username': 'System'}, broadcast=True)
    else:
        return False  # Reject unauthenticated connections

@socketio.on('disconnect')
def handle_disconnect():
    username = getattr(current_user, 'username', 'User') if current_user.is_authenticated else 'User'
    print(f'{username} disconnected.')
    
    # Handle general chat disconnect
    if current_user.is_authenticated:
        emit('message_response', {'message': f'{username} has left the chat.', 'username': 'System'}, broadcast=True)
    
    # Handle video call room cleanup
    sid_to_remove = request.sid
    rooms_to_clean = []
    
    for room, sids in call_rooms.items():
        if sid_to_remove in sids:
            rooms_to_clean.append(room)
    
    for room in rooms_to_clean:
        # Remove the disconnected user
        call_rooms[room].remove(sid_to_remove)
        
        # Notify remaining peers
        if call_rooms[room]:
            emit('peer_left', {'peer': username}, room=room)
        
        # Clean up empty room
        if not call_rooms[room]:
            del call_rooms[room]
            
        print(f"Cleaned up call room {room} after user {sid_to_remove} disconnected.")

# HELPER FUNCTION to save uploaded pictures
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

# UPDATED ROUTE: Account management
@main.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

# NEW ROUTE: User's public profile page with their posts
@main.route("/user/<string:username>")
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
                .order_by(Post.date_posted.desc())\
                .all()
    return render_template('user_posts.html', posts=posts, user=user)

@main.route("/messages")
@login_required
def messages():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('messages.html', title='Messages', users=users)

# NEW ROUTE: Private chat page
@main.route("/messages/<username>")
@login_required
def private_chat(username):
    recipient = User.query.filter_by(username=username).first_or_404()
    if recipient == current_user:
        flash('You cannot chat with yourself.', 'danger')
        return redirect(url_for('main.messages'))
    
    # Fetch message history
    messages = Message.query.filter(
        or_(
            (Message.sender_id == current_user.id) & (Message.recipient_id == recipient.id),
            (Message.sender_id == recipient.id) & (Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    return render_template('private_chat.html', title=f'Chat with {username}', recipient=recipient, messages=messages)


# --- SocketIO Event Handlers for Private Chat ---

@socketio.on('join')
def on_join(data):
    """User joins a private chat room"""
    username = data['username']
    room = data['room']
    join_room(room)
    print(f'{username} has entered the room: {room}')

@socketio.on('leave')
def on_leave(data):
    """User leaves a private chat room"""
    username = data['username']
    room = data['room']
    leave_room(room)
    print(f'{username} has left the room: {room}')

@socketio.on('private_message')
def handle_private_message(data):
    """Handles sending and storing private messages."""
    room = data['room']
    message_body = data['message']
    
    sender = User.query.filter_by(username=data['sender']).first()
    recipient = User.query.filter_by(username=data['recipient']).first()

    if not sender or not recipient:
        return # Should not happen

    # Save message to database
    msg = Message(author=sender, recipient=recipient, body=message_body)
    db.session.add(msg)
    db.session.commit()

    # Emit message to the room
    payload = {
        'message': message_body,
        'sender': sender.username,
        'recipient': recipient.username,
        'timestamp': msg.timestamp.strftime('%b %d, %I:%M %p')
    }
    emit('new_private_message', payload, room=room)
    print(f"Message sent from {sender.username} to {recipient.username} in room {room}")

# Video call page route
@main.route("/call/<username>")
@login_required
def video_call(username):
    recipient = User.query.filter_by(username=username).first_or_404()
    # Users cannot call themselves
    if recipient == current_user:
        flash("You cannot start a call with yourself.", "danger")
        return redirect(url_for('main.messages'))
    return render_template('video_call.html', title=f'Video Call with {username}', recipient=recipient)


# --- SocketIO Event Handlers for WebRTC Signaling (IMPROVED LOGIC) ---

@socketio.on('join_call')
def on_join_call(data):
    """
    A user joins a room for a specific video call.
    This new logic ensures two peers are connected before starting the offer process.
    """
    room = data['room']
    join_room(room)
    
    # Add peer to our room state
    if room not in call_rooms:
        call_rooms[room] = []
    call_rooms[room].append(request.sid)

    print(f"{current_user.username} (SID: {request.sid}) has joined the call room: {room}")

    # When two peers have joined, signal them to get ready.
    if len(call_rooms[room]) == 2:
        # Emit to both peers that they are connected and can start preparing.
        emit('peers_connected', {'peer1': call_rooms[room][0], 'peer2': call_rooms[room][1]}, room=room)
        print(f"Two peers connected in room {room}. Signalling them to prepare.")

@socketio.on('webrtc_signal')
def on_webrtc_signal(data):
    """
    Generic handler to relay any WebRTC signal (offer, answer, ice-candidate)
    to the other peer in the room.
    """
    room = data['room']
    signal = data['signal']
    
    # Find the other peer's SID
    if room in call_rooms and len(call_rooms[room]) == 2:
        peer1_sid, peer2_sid = call_rooms[room]
        target_sid = peer2_sid if request.sid == peer1_sid else peer1_sid
        emit('webrtc_signal', signal, room=target_sid)
        # print(f"Relaying signal from {request.sid} to {target_sid} in room {room}")

@socketio.on('leave_call')
def on_leave_call(data):
    """A user intentionally leaves a video call room."""
    room = data['room']
    leave_room(room)
    
    # Notify the other peer that the user has left
    if room in call_rooms:
        emit('peer_left', {'peer': current_user.username}, room=room, skip_sid=request.sid)
        # Clean up the room state
        if room in call_rooms:
            del call_rooms[room]

    print(f"{current_user.username} has left the call room: {room}")

@socketio.on('disconnect')
def handle_disconnect():
    username = getattr(current_user, 'username', 'User')
    print(f'{username} disconnected.')
    emit('message_response', {'message': f'{username} has left the chat.', 'username': 'System'}, broadcast=True)
