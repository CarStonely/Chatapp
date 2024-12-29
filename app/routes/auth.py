from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from app import bcrypt
import mysql.connector

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Use current_app to access the app context
        conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            user_id, password_hash = row
            if bcrypt.check_password_hash(password_hash, password):
                session['user_id'] = user_id
                session['username'] = username
                return redirect(url_for('chat.index'))

        return "Invalid credentials!"
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
            conn.commit()
        except mysql.connector.Error:
            conn.rollback()
            return "Error registering user"
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
