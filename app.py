from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Load environment variables from .env
load_dotenv()

app.secret_key = os.getenv('SECRET_KEY')
socketio = SocketIO(app)

# Configure your MySQL connection using environment variables
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'connection_timeout': 10  # Timeout after 10 seconds
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the chat history from the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT username, message, DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i:%s') AS formatted_timestamp
            FROM messages
            ORDER BY timestamp ASC
        """)
        chat_history = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template('chat.html', chat_history=chat_history, room='general', rooms=[])  # Pass rooms as empty for this route

@app.route('/rooms')
def rooms():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch all rooms
        cursor.execute("SELECT name FROM rooms ORDER BY created_at DESC")
        rooms = [row['name'] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

    return render_template('rooms.html', rooms=rooms)

@app.route('/create_room', methods=['POST'])
def create_room():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    room_name = request.form['room'].strip()

    # Validate the room name
    if not room_name or len(room_name) > 50:
        return "Invalid room name!", 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Check for duplicate room name
        cursor.execute("SELECT id FROM rooms WHERE name = %s", (room_name,))
        if cursor.fetchone():
            return "Room already exists!", 400

        # Insert the new room
        cursor.execute(
            "INSERT INTO rooms (name, created_by) VALUES (%s, %s)",
            (room_name, session['user_id'])
        )
        conn.commit()
    except mysql.connector.Error as err:
        conn.rollback()
        return f"Database error: {err}", 500
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('chat_room', room=room_name))

@app.route('/chat/<room>')
def chat_room(room):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        # Validate room existence
        cursor.execute("SELECT id FROM rooms WHERE name = %(room)s", {"room": room})
        room_record = cursor.fetchone()
        if not room_record:
            print(f"Debug: Room '{room}' not found in rooms table.")
            return "Room not found!", 404

        # Fetch chat history for the room
        cursor.execute("""
            SELECT username, message, DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i:%s') AS formatted_timestamp
            FROM messages
            WHERE room = %(room)s
            ORDER BY timestamp ASC
        """, {"room": room})
        chat_history = cursor.fetchall()

        # Fetch all available rooms
        cursor.execute("SELECT name FROM rooms ORDER BY created_at DESC")
        rooms = [row['name'] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

    return render_template('chat.html', chat_history=chat_history, room=room, rooms=rooms)

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Attempt to insert user
        try:
            sql = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
            cursor.execute(sql, (username, password_hash))
            conn.commit()
        except mysql.connector.Error as err:
            conn.rollback()
            return f"Error: {err}"
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Fetch user by username
        cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if row:
            user_id, password_hash = row
            if bcrypt.check_password_hash(password_hash, password):
                session['user_id'] = user_id
                session['username'] = username
                return redirect(url_for('chat'))

        return "Invalid credentials!"

    return render_template('login.html')

@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = session.get('username', 'Anonymous')
    join_room(room)
    emit('notification', {'user': username, 'message': f"has joined {room}"}, room=room)
    print(f"{username} joined room: {room}")

@socketio.on('message')
def handle_message(data):
    username = session.get('username', 'Anonymous')
    message = data.get('message', '')
    room = data.get('room', 'general')  # Default to 'general' if no room is provided
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Save the message to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO messages (username, message, room, timestamp) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (username, message, room, timestamp))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    # Broadcast the message to the specific room
    emit('message', {'user': username, 'message': message, 'timestamp': timestamp}, room=room)

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    username = session.get('username', 'Anonymous')
    leave_room(room)
    emit('notification', {'user': username, 'message': f"has left {room}"}, room=room)
    print(f"{username} left room: {room}")

# Use socketio.run() instead of app.run()
if __name__ == '__main__':
    socketio.run(app, debug=True)
