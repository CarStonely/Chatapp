from flask_socketio import emit, join_room, leave_room
from flask import Blueprint, session, current_app
from datetime import datetime
import mysql.connector
from app import socketio  # Import socketio from app/__init__.py

socket_bp = Blueprint('socket_events', __name__)

@socketio.on('join')
def handle_join(data):
    """
    Handle when a user joins a chat room.
    """
    room = data.get('room')
    username = session.get('username', 'Anonymous')

    if room:
        join_room(room)
        emit('notification', {
            'user': username,
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
        # Use current_app to access app configuration
        conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
        cursor = conn.cursor()
        try:
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

        # Broadcast the message to the room
        emit('message', {
            'user': username,
            'message': message,
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
