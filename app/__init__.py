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

    # Configure MySQL connection
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
    from app.routes import blueprints  # Import blueprints from routes/__init__.py
    for bp in blueprints:
        app.register_blueprint(bp)

    return app
