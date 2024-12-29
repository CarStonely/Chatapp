from flask import Blueprint, request, redirect, url_for, session, current_app
import mysql.connector

rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/', methods=['GET'])
def list_rooms():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Use current_app to access the app configuration
    conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name FROM rooms ORDER BY created_at DESC")
    rooms = [row['name'] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    return {"rooms": rooms}

@rooms_bp.route('/create', methods=['POST'])
def create_room():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    room_name = request.form['room'].strip()

    # Use current_app to access the app configuration
    conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO rooms (name, created_by) VALUES (%s, %s)", (room_name, session['user_id']))
        conn.commit()
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error creating room: {e}")
        return "Error creating room!"
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('chat.index'))
