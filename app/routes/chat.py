
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

    # Use current_app to access the app configuration
    conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM rooms WHERE name = %s", (room,))
    room_exists = cursor.fetchone()
    if not room_exists:
        return "Room not found!", 404

    cursor.execute("""
        SELECT username, message, timestamp
        FROM messages
        WHERE room = %s
        ORDER BY timestamp ASC
    """, (room,))
    chat_history = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('chat.html', room=room, chat_history=chat_history)
