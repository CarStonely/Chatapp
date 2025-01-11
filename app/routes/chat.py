from flask import Blueprint, render_template, current_app, session, redirect, url_for
import mysql.connector

from .socket_events import generate_room_id

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Get a connection from the pool
    conn = current_app.config['DB_POOL'].get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT name FROM rooms ORDER BY created_at DESC")
        rooms = [row['name'] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return "Error loading rooms!", 500
    finally:
        cursor.close()
        conn.close()

    return render_template('room_selector.html', rooms=rooms)

@chat_bp.route('/<room>')
def room(room):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = current_app.config['DB_POOL'].get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch list of all available rooms
        cursor.execute("SELECT name FROM rooms ORDER BY created_at DESC")
        rooms = [row['name'] for row in cursor.fetchall()]

        # Ensure the room exists
        if room not in rooms:
            return "Room not found!", 404

        # Fetch chat history for the current room, including image_url
        cursor.execute("""
            SELECT m.username, m.message, m.timestamp, m.image_url, u.profile_picture
            FROM messages m
            JOIN users u ON m.username = u.username
            WHERE m.room = %s
            ORDER BY m.timestamp ASC
        """, (room,))
        chat_history = cursor.fetchall()

        # Fetch all users for the side container
        cursor.execute("SELECT username, profile_picture FROM users ORDER BY username ASC")
        all_users = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return "Error loading chat room!", 500
    finally:
        cursor.close()
        conn.close()

    # Pass the rooms, current room, chat history, and all users to the template
    return render_template('chat.html', room=room, chat_history=chat_history, rooms=rooms, all_users=all_users)

@chat_bp.route('/dm/<target_username>')
def direct_message(target_username):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    current_user_id = session['user_id']
    conn = current_app.config['DB_POOL'].get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Retrieve target user details
        cursor.execute("SELECT id, username, profile_picture FROM users WHERE username = %s", (target_username,))
        target_user = cursor.fetchone()
        if not target_user:
            return "User not found", 404

        # Check for existing DM room between current user and target user
        cursor.execute("""
            SELECT dr.id, dr.room_name 
            FROM dm_rooms dr
            JOIN dm_room_participants drp1 ON dr.id = drp1.room_id
            JOIN dm_room_participants drp2 ON dr.id = drp2.room_id
            WHERE drp1.user_id = %s AND drp2.user_id = %s
        """, (current_user_id, target_user['id']))
        room_data = cursor.fetchone()

        if room_data:
            dm_room_id = room_data['id']
            room_name = room_data['room_name']
        else:
            # Generate a unique room name for the DM
            generated_room_name = generate_room_id(current_user_id, target_user['id'])

            # Create a new room in the 'rooms' table to satisfy foreign key constraints
            cursor.execute("""
                INSERT INTO rooms (name, created_by, created_at, private) 
                VALUES (%s, %s, NOW(), 1)
            """, (generated_room_name, current_user_id))
            conn.commit()

            # Create a new DM room in 'dm_rooms'
            cursor.execute("INSERT INTO dm_rooms (room_name) VALUES (%s)", (generated_room_name,))
            dm_room_id = cursor.lastrowid

            # Add both users as participants in 'dm_room_participants'
            cursor.execute("INSERT INTO dm_room_participants (room_id, user_id) VALUES (%s, %s)", (dm_room_id, current_user_id))
            cursor.execute("INSERT INTO dm_room_participants (room_id, user_id) VALUES (%s, %s)", (dm_room_id, target_user['id']))
            conn.commit()

            room_name = generated_room_name

        # Fetch DM message history for this room, including image_url
        cursor.execute("""
            SELECT m.username, m.message, m.timestamp, m.image_url, u.profile_picture
            FROM messages m
            JOIN users u ON m.username = u.username
            WHERE m.room = %s
            ORDER BY m.timestamp ASC
        """, (room_name,))
        chat_history = cursor.fetchall()

        # Fetch all users for the side container
        cursor.execute("SELECT username, profile_picture FROM users ORDER BY username ASC")
        all_users = cursor.fetchall()

        rooms = []  # No need for room selection in DM context

        # Create a user-friendly display name for the DM
        dm_display_name = f"Chat with {target_user['username']}"

    except mysql.connector.Error as e:
        print(e)
        return "Error loading DM", 500
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'chat.html', 
        room=room_name, 
        chat_history=chat_history, 
        rooms=rooms, 
        all_users=all_users,
        dm_display_name=dm_display_name
    )
