# app/__init__.py

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from dotenv import load_dotenv
from datetime import timedelta
import os
from mysql.connector import pooling, Error
# Initialize Extensions
bcrypt = Bcrypt()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.secret_key = os.getenv('SECRET_KEY')

    # Secure session cookie settings
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    # Database connection pooling configuration
    try:
        app.config['DB_POOL'] = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=30,
            pool_reset_session=True,
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
        )
        app.logger.info("Database connection pool created successfully.")
    except Error as e:
        app.logger.error(f"Error creating DB_POOL: {e}", exc_info=True)
        raise

    # Initialize Extensions with App
    bcrypt.init_app(app)
    socketio.init_app(app)
     # Initialize extensions
    socketio.init_app(app)


    # Register Blueprints  
    from app.routes import blueprints
    for bp in blueprints:
        app.register_blueprint(bp)


    return app
