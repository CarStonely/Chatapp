
from flask import Blueprint, render_template, current_app, session, redirect, url_for
import mysql.connector

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Use current_app to access the app configuration
    conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name FROM rooms ORDER BY created_at DESC")
    rooms = [row['name'] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    return render_template('room_selector.html', rooms=rooms)

@chat_bp.route('/<room>')
def room(room):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Fetch all available rooms
    conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name FROM rooms ORDER BY created_at DESC")
    rooms = [row['name'] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    # Ensure the room exists
    if room not in rooms:
        return "Room not found!", 404

    # Fetch chat history for the current room
    conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT m.username, m.message, m.timestamp, u.profile_picture
    FROM messages m
    JOIN users u ON m.username = u.username
    WHERE m.room = %s
    ORDER BY m.timestamp ASC
""", (room,))
    chat_history = cursor.fetchall()
    cursor.close()
    conn.close()

    # Pass the rooms and current room to the template
    return render_template('chat.html', room=room, chat_history=chat_history, rooms=rooms)

