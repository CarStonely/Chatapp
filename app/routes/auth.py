import os  # Provides functions for interacting with the operating system, such as handling file paths
from flask import Blueprint, flash, jsonify, render_template, request, redirect, url_for, session, current_app  # Flask modules for routing, flashing messages, handling requests, and session management
from app import bcrypt  # Bcrypt for hashing passwords and checking password hashes
import mysql.connector  # MySQL connector for database interaction
from werkzeug.utils import secure_filename  # Utility to safely handle uploaded filenames
import re  # Regular expressions for validating username format

# Create a Blueprint for authentication-related routes
auth_bp = Blueprint('auth', __name__)

# Function to validate username format using a regular expression
def is_valid_username(username):
    # Username must be 3 to 20 characters long, containing only letters, numbers, and underscores
    return re.match(r'^[a-zA-Z0-9_]{3,20}$', username)

# Allowed file extensions for profile picture uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Maximum allowed content length for file uploads (2 MB)
MAX_CONTENT_LENGTH = 2 * 1024 * 1024

# Function to check if a file has an allowed extension
def is_allowed_file(filename):
    # Check if the file has an extension and if it is in the allowed list
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for login, supporting both GET and POST methods
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Handle form submission
        email = request.form['email'].strip().lower()  # Retrieve and sanitize email input
        password = request.form['password']  # Retrieve password input

        # Get a database connection from the connection pool
        conn = current_app.config['DB_POOL'].get_connection()
        cursor = conn.cursor()  # Create a cursor to execute queries

        try:
            # Query to check if a user with the provided email exists
            cursor.execute("SELECT id, username, password_hash FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()  # Fetch one result

            if user:  # If a user is found
                user_id, username, password_hash = user  # Unpack the result
                # Check if the provided password matches the stored hash
                if bcrypt.check_password_hash(password_hash, password):
                    session['user_id'] = user_id  # Set session variables for user ID
                    session['username'] = username  # Set session variable for username
                    flash("Login successful!", "success")  # Display success message
                    return redirect(url_for('chat.index'))  # Redirect to chat page
            flash("Incorrect email or password!", "error")  # Display error message if credentials are incorrect
        except mysql.connector.Error as e:
            print(f"Database error during login: {e}")  # Log database error
        finally:
            cursor.close()  # Close the cursor
            conn.close()  # Close the connection

        return redirect(url_for('auth.login'))  # Redirect back to login page

    return render_template('login.html')  # Render the login page for GET requests

# Route for user registration
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Handle form submission
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        # Get a database connection from the connection pool
        conn = current_app.config['DB_POOL'].get_connection()
        cursor = conn.cursor()

        try:
            # Check if a user with the provided email or username already exists
            cursor.execute("SELECT id FROM users WHERE email = %s OR username = %s", (email, username))
            existing_user = cursor.fetchone()

            if existing_user:
                error = "Username or email already exists!"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'error': error}), 400  # Bad Request
                else:
                    flash(error, "error")
                    return redirect(url_for('auth.register'))

            # Hash the password using bcrypt
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            default_avatar = '/static/images/default_avatar.png'

            # Insert the new user into the database
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, profile_picture)
                VALUES (%s, %s, %s, %s)
            """, (username, email, password_hash, default_avatar))
            conn.commit()

            success_message = "Registration successful! You can now log in."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': success_message}), 201  # Created
            else:
                flash(success_message, "success")
                return redirect(url_for('auth.login'))

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Database error during registration: {e}")  # Consider using proper logging
            error = "Error registering user. Please try again."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': error}), 500  # Internal Server Error
            else:
                flash(error, "error")
                return redirect(url_for('auth.register'))
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')  # Render the registration page for GET requests

# Route for viewing and updating the user profile
@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:  # Check if the user is logged in
        return redirect(url_for('auth.login'))  # Redirect to login page if not logged in

    # Get a database connection from the connection pool
    conn = current_app.config['DB_POOL'].get_connection()
    cursor = conn.cursor(dictionary=True)  # Use a dictionary cursor for easier access to results

    try:
        if request.method == 'POST':  # Handle form submission for profile update
            bio = request.form.get('bio', '').strip()  # Retrieve and sanitize bio input
            profile_picture = None  # Initialize profile picture variable

            # Handle file upload if a file is provided
            if 'profile_picture' in request.files and request.files['profile_picture'].filename != '':
                file = request.files['profile_picture']
                if file:  # If a file is provided
                    filename = secure_filename(file.filename)  # Secure the filename
                    file_path = os.path.join(current_app.static_folder, 'uploads', filename)  # Set file path
                    file.save(file_path)  # Save the file to the server
                    profile_picture = f'/static/uploads/{filename}'  # Set profile picture path

            # Update the user's bio and profile picture in the database
            update_query = """
                UPDATE users
                SET bio = %s
            """
            params = [bio]  # Initialize query parameters with bio

            # Add profile picture to the query if a file was uploaded
            if profile_picture:
                update_query += ", profile_picture = %s"
                params.append(profile_picture)

            update_query += " WHERE id = %s"  # Add condition to update the correct user
            params.append(session['user_id'])  # Add user ID to query parameters

            cursor.execute(update_query, tuple(params))  # Execute the update query
            conn.commit()  # Commit the transaction

        # Fetch current profile data to display
        cursor.execute("SELECT username, bio, profile_picture FROM users WHERE id = %s", (session['user_id'],))
        user_profile = cursor.fetchone()  # Fetch one result
    except mysql.connector.Error as e:
        print(f"Database error during profile update: {e}")  # Log database error
        flash("Error updating profile. Please try again.", "error")  # Display error message
    finally:
        cursor.close()  # Close the cursor
        conn.close()  # Close the connection

    return render_template('profile.html', user=user_profile)  # Render profile page with user data

# Route for logging out the user
@auth_bp.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash("You have been logged out successfully.", "success")  # Display success message
    return redirect(url_for('auth.login'))  # Redirect to login page

# Route for viewing another user's profile by username
@auth_bp.route('/profile/<username>', methods=['GET'])
def view_profile(username):
    # Get a database connection from the connection pool
    conn = current_app.config['DB_POOL'].get_connection()
    cursor = conn.cursor(dictionary=True)  # Use a dictionary cursor for easier access to results

    try:
        # Query to fetch the user's profile by username
        cursor.execute("SELECT username, bio, profile_picture FROM users WHERE username = %s", (username,))
        user_profile = cursor.fetchone()  # Fetch one result

        if not user_profile:  # If no profile is found
            return "User not found", 404  # Return a 404 error
    except mysql.connector.Error as e:
        print(f"Database error during profile viewing: {e}")  # Log database error
        return "Error loading profile!", 500  # Return a 500 error
    finally:
        cursor.close()  # Close the cursor
        conn.close()  # Close the connection

    return render_template('view_profile.html', user=user_profile)  # Render profile page with user data
