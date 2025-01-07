from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
import mysql.connector

rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/', methods=['GET'])
def list_rooms():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Get a connection from the pool
    conn = current_app.config['DB_POOL'].get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch chat rooms
        cursor.execute("SELECT name FROM rooms ORDER BY created_at DESC")
        rooms = [row['name'] for row in cursor.fetchall()]

        # Fetch all users (excluding the current user if needed)
        cursor.execute("SELECT id, username FROM users ORDER BY username ASC")
        users = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return "Error loading rooms!", 500
    finally:
        cursor.close()
        conn.close()

    # Pass both rooms and users to the template
    return render_template('room_selector.html', rooms=rooms, users=users)


@rooms_bp.route('/create', methods=['POST'])
def create_room():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    room_name = request.form['room'].strip()

    # Get a connection from the pool
    conn = current_app.config['DB_POOL'].get_connection()
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
