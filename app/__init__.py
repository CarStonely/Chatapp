from datetime import timedelta
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

bcrypt = Bcrypt()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.secret_key = os.getenv('SECRET_KEY')


    # Secure session cookie settings
    app.config['SESSION_COOKIE_SECURE'] = True  # Send cookies over HTTPS only
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # Mitigate CSRF
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session timeout

    # Database configuration
    app.config['DB_CONFIG'] = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'connection_timeout': 10
    }

    bcrypt.init_app(app)
    socketio.init_app(app)

    # Register blueprints
    from app.routes import blueprints
    for bp in blueprints:
        app.register_blueprint(bp)

    return app
