from app import create_app, socketio

# Create the Flask app using the factory function
app = create_app()

if __name__ == '__main__':
    # Use SocketIO to run the app
    socketio.run(app, debug=True)
