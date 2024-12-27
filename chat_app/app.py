from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)
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

    return render_template('chat.html', chat_history=chat_history)

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

@socketio.on('message')
def handle_message(data):
    username = session.get('username', 'Anonymous')
    message = data.get('message', '')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Generate formatted timestamp

    # Save the message to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO messages (username, message, timestamp) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, message, timestamp))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    # Broadcast the message, including the timestamp
    emit('message', {'user': username, 'message': message, 'timestamp': timestamp}, broadcast=True)

# Use socketio.run() instead of app.run()
if __name__ == '__main__':
    socketio.run(app, debug=True)
