import os
from flask import Blueprint, flash, render_template, request, redirect, url_for, session, current_app
from app import bcrypt
import mysql.connector
from werkzeug.utils import secure_filename
import re

auth_bp = Blueprint('auth', __name__)

# Function to validate username format
def is_valid_username(username):
    return re.match(r'^[a-zA-Z0-9_]{3,20}$', username)

# Constants for file upload validation
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB limit

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        # Check if the email exists in the database
        conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            user_id, username, password_hash = user
            if bcrypt.check_password_hash(password_hash, password):
                # Set session variables
                session['user_id'] = user_id
                session['username'] = username
                flash("Login successful!", "success")
                return redirect(url_for('chat.index'))

        flash("Incorrect email or password!", "error")
        return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        # Check if the email or username already exists
        conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s OR username = %s", (email, username))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username or email already exists!", "error")
            return redirect(url_for('auth.register'))

        # Hash the password and insert the new user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        default_avatar = '/static/images/default_avatar.png'

        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, profile_picture)
                VALUES (%s, %s, %s, %s)
            """, (username, email, password_hash, default_avatar))
            conn.commit()
        except mysql.connector.Error as e:
            conn.rollback()
            flash("Error registering user. Please try again.", "error")
        finally:
            cursor.close()
            conn.close()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
    cursor = conn.cursor(dictionary=True)
    
    
    
    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()
        profile_picture = None

        # Handle file upload
        if 'profile_picture' in request.files and request.files['profile_picture'].filename != '':
            file = request.files['profile_picture']
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.static_folder, 'uploads', filename)
                file.save(file_path)
                profile_picture = f'/static/uploads/{filename}'

        # Update database
        update_query = """
            UPDATE users
            SET bio = %s
        """
        params = [bio]

        # Add profile picture to the query only if a file was uploaded
        if profile_picture:
            update_query += ", profile_picture = %s"
            params.append(profile_picture)

        update_query += " WHERE id = %s"
        params.append(session['user_id'])

        cursor.execute(update_query, tuple(params))
        conn.commit()

    # Fetch current profile data
    cursor.execute("SELECT username, bio, profile_picture FROM users WHERE id = %s", (session['user_id'],))
    user_profile = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('profile.html', user=user_profile)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile/<username>', methods=['GET'])
def view_profile(username):
    conn = mysql.connector.connect(**current_app.config['DB_CONFIG'])
    cursor = conn.cursor(dictionary=True)
    
    # Fetch the user's profile by username
    cursor.execute("SELECT username, bio, profile_picture FROM users WHERE username = %s", (username,))
    user_profile = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user_profile:
        return "User not found", 404

    return render_template('view_profile.html', user=user_profile)


