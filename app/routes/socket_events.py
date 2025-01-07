# socket_events.py
from flask_socketio import emit, join_room, leave_room
from flask import Blueprint, session, current_app
from datetime import datetime
import mysql.connector
from app import socketio  # Import socketio from app/__init__.py

socket_bp = Blueprint('socket_events', __name__)

# Dictionary to track online users per room
# Structure: {room1: {username1: profile_picture1, username2: profile_picture2}, room2: {...}, ...}
online_users = {}

def generate_room_id(user1_id, user2_id):
    """Ensure both IDs are integers and return a consistent room ID."""
    user1_id = int(user1_id)
    user2_id = int(user2_id)
    return f"dm_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"

def fetch_profile_picture(username):
    """Fetch the profile picture URL for a given username."""
    conn = current_app.config['DB_POOL'].get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT profile_picture FROM users WHERE username = %s", (username,))
        user_info = cursor.fetchone()
        return user_info['profile_picture'] if user_info and user_info['profile_picture'] else '/static/images/default_avatar.png'
    except mysql.connector.Error as err:
        print(f"Database error while fetching profile picture: {err}")
        return '/static/images/default_avatar.png'
    finally:
        cursor.close()
        conn.close()

def get_all_online_users(room):
    """Retrieve all online users in a specific room with their profile pictures."""
    users_in_room = online_users.get(room, {})
    user_list = [{'username': username, 'profile_picture': profile_pic} for username, profile_pic in users_in_room.items()]
    return user_list

@socketio.on('join')
def handle_join(data):
    """
    Handle when a user joins a chat room, with authorization for DM rooms based on the new schema.
    """
    room = data.get('room')
    username = session.get('username', 'Anonymous')
    user_id = session.get('user_id')

    # For DM rooms, verify participant status using the new schema
    if room and room.startswith('dm_'):
        conn = current_app.config['DB_POOL'].get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Check if user_id is a participant of the DM room
            cursor.execute("""
                SELECT drp.user_id
                FROM dm_rooms dr
                JOIN dm_room_participants drp ON dr.id = drp.room_id
                WHERE dr.room_name = %s AND drp.user_id = %s
            """, (room, user_id))
            is_participant = cursor.fetchone() is not None
            if not is_participant:
                print(f"Unauthorized DM join attempt by user {user_id} to room {room}")
                return  # Prevent joining if not authorized
        except mysql.connector.Error as e:
            print(f"DB error during join auth: {e}")
            return
        finally:
            cursor.close()
            conn.close()

    # Proceed with joining the room if not a restricted DM or after authorization
    if room:
        profile_picture = fetch_profile_picture(username)

        # Initialize the online_users list for the room if not already present
        if room not in online_users:
            online_users[room] = {}

        # Add the user to the online users list for the room
        online_users[room][username] = profile_picture

        # Make the user join the Socket.IO room
        join_room(room)

        # Emit updates about online users in the room to all clients in that room
        emit('update_users', get_all_online_users(room), room=room)

        # Notify other users in the room that a new user has joined
        emit('notification', {
            'user': username,
            'profile_picture': profile_picture,
            'message': f"{username} has joined the room."
        }, room=room, include_self=False)

        print(f"{username} joined room: {room}")
        
@socketio.on('message')
def handle_message(data):
    """
    Handle when a user sends a message in a room.
    Ensures that for DM rooms, the room exists in the `dm_rooms` table
    before inserting the message.
    """
    username = session.get('username', 'Anonymous')
    user_id = session.get('user_id')
    message = data.get('message', '').strip()
    room = data.get('room')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if message and room:
        # Check if the room is a DM room
        if room.startswith('dm_'):
            try:
                conn_room = current_app.config['DB_POOL'].get_connection()
                cursor_room = conn_room.cursor(dictionary=True)

                # Check if the DM room exists in `dm_rooms`
                cursor_room.execute("SELECT 1 FROM dm_rooms WHERE room_name = %s", (room,))
                if not cursor_room.fetchone():
                    print(f"Unauthorized access or non-existent DM room: {room}")
                    return  # Abort message handling if the room doesn't exist

            except mysql.connector.Error as e:
                print(f"Error checking DM room existence: {e}")
                return
            finally:
                cursor_room.close()
                conn_room.close()

        # Fetch profile picture for the sender
        profile_picture = fetch_profile_picture(username)

        # Insert the message into the `messages` table
        conn = current_app.config['DB_POOL'].get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO messages (username, message, room, timestamp)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (username, message, room, timestamp))
            conn.commit()
            print(f"Stored message for room {room}: {message}")
        except mysql.connector.Error as err:
            print(f"Database error during message insertion: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        # Emit the message to all clients in the room
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

        # Remove user from the specific room's online users
        if room in online_users and username in online_users[room]:
            del online_users[room][username]
            # If no users left in the room, remove the room from online_users
            if not online_users[room]:
                del online_users[room]

        # Emit an update to all clients in the room about the online users
        emit('update_users', get_all_online_users(room), room=room)

        # Notify other users in the room
        emit('notification', {
            'user': username,
            'message': f"{username} has left the room."
        }, room=room, include_self=False)

        print(f"{username} left room: {room}")

@socketio.on('connect')
def handle_connect():
    """
    Handle when a user connects to the server.
    """
    user_id = session.get('user_id')
    if user_id:
        join_room(f"user_{user_id}")
        print(f"User with ID {user_id} connected and joined personal room.")

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle when a user disconnects from the server.
    """
    username = session.get('username', 'Anonymous')

    # Iterate through all rooms and remove the user from online_users
    rooms_to_remove = []
    for room, users in online_users.items():
        if username in users:
            del online_users[room][username]
            # If no users left in the room, mark it for removal
            if not online_users[room]:
                rooms_to_remove.append(room)
            # Notify other users in the room
            emit('notification', {
                'user': username,
                'message': f"{username} has disconnected."
            }, room=room, include_self=False)
            # Emit updated online users list to all clients in the room
            emit('update_users', get_all_online_users(room), room=room)
            print(f"{username} removed from room: {room}")

    # Remove empty rooms
    for room in rooms_to_remove:
        del online_users[room]

    print(f"{username} disconnected.")

@socketio.on('typing')
def handle_typing(data):
    """
    Handle when a user starts typing in a room.
    """
    room = data.get('room')
    username = session.get('username', 'Anonymous')

    emit('user_typing', {
        'username': username,
        'action': 'typing'
    }, room=room, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    """
    Handle when a user stops typing in a room.
    """
    room = data.get('room')
    username = session.get('username', 'Anonymous')

    emit('user_typing', {
        'username': username,
        'action': 'stopped'
    }, room=room, include_self=False)
