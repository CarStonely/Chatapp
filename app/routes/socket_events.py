from flask_socketio import emit, join_room, leave_room
from flask import Blueprint, session, current_app
from datetime import datetime
import mysql.connector
from app import socketio  # Import socketio from app/__init__.py
from app.utils import get_room_id



socket_bp = Blueprint('socket_events', __name__)

@socketio.on('join')
def handle_join(data):
    """
    Handle when a user joins a chat room.
    """
    room = data.get('room')
    username = session.get('username', 'Anonymous')

    if room:
        conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
        cursor = conn.cursor(dictionary=True)
        try:
            # Fetch the user's profile picture from the database
            cursor.execute("SELECT profile_picture FROM users WHERE username = %s", (username,))
            user_info = cursor.fetchone()
            profile_picture = user_info['profile_picture'] if user_info else '/static/images/default_avatar.png'

        finally:
            cursor.close()
            conn.close()

        # Join the room
        join_room(room)

        # Notify other users in the room
        emit('notification', {
            'user': username,
            'profile_picture': profile_picture,
            'message': f"{username} has joined the room."
        }, room=room)

        print(f"{username} joined room: {room}")
    
@socketio.on('message')
def handle_message(data):
    """
    Handle when a user sends a message in a room.
    """
    username = session.get('username', 'Anonymous')
    message = data.get('message', '').strip()
    room = data.get('room')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if message and room:
        conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
        cursor = conn.cursor(dictionary=True)
        try:
            # Dynamically fetch the latest profile picture
            cursor.execute("SELECT profile_picture FROM users WHERE username = %s", (username,))
            user_info = cursor.fetchone()
            profile_picture = user_info['profile_picture'] if user_info else '/static/images/default_avatar.png'

            # Insert the message into the database
            sql = """
                INSERT INTO messages (username, message, room, timestamp)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (username, message, room, timestamp))
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        # Broadcast the message with the dynamically fetched profile picture
        emit('message', {
            'user': username,
            'message': message,
            'profile_picture': profile_picture,
            'timestamp': timestamp
        }, room=room)
        
@socketio.on('leave')
def handle_leave(data):
    """
    Handle when a user leaves a chat room.
    """
    room = data.get('room')
    username = session.get('username', 'Anonymous')

    if room:
        leave_room(room)
        emit('notification', {
            'user': username,
            'message': f"{username} has left the room."
        }, room=room)
        print(f"{username} left room: {room}")

@socketio.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    if user_id:
        join_room(f"user_{user_id}")

@socketio.on('typing')
def handle_typing(data):
    """
    data = {
       'room': 'room_name'
    }
    """
    user_id = session.get('user_id')
    username = session.get('username', 'Anonymous')
    room = data.get('room')

    # Broadcast to others in the same room that this user is typing
    # (We could also include a timestamp or user_id if needed)
    emit('user_typing', {
        'username': username,
        'action': 'typing'
    }, room=room, include_self=False)
    
@socketio.on('stop_typing')
def handle_stop_typing(data):
    """
    data = {
       'room': 'room_name'
    }
    """
    username = session.get('username', 'Anonymous')
    room = data.get('room')

    emit('user_typing', {
        'username': username,
        'action': 'stopped'
    }, room=room, include_self=False)

