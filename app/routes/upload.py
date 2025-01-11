from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    # Validate extension (e.g., .png, .jpg, .jpeg)
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Invalid file extension'}), 400

    # Use secure_filename to avoid directory traversal
    filename = secure_filename(file.filename)

    # Path where you want to store images (e.g., static/uploads/)
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)  # Create folder if doesn't exist

    # Construct the full file path
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)  # Save image to server

    # Build the URL to serve the image
    image_url = f'/static/uploads/{filename}'

    # Return JSON with success = True and the image_url
    return jsonify({'success': True, 'image_url': image_url})
