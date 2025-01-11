# app/routes/__init__.py

# Import all blueprints from their respective modules
from .auth import auth_bp
from .chat import chat_bp
from .rooms import rooms_bp
from .socket_events import socket_bp
from .upload import upload_bp

# A list of all blueprints to be registered in the app factory
blueprints = [
    auth_bp,
    chat_bp,
    rooms_bp,
    socket_bp,
    upload_bp
]