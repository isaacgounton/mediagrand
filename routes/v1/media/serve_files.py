from flask import Blueprint, send_from_directory, current_app
import os
from config import LOCAL_STORAGE_PATH
import mimetypes

v1_media_serve_files_bp = Blueprint('v1_media_serve_files', __name__, url_prefix='/v1/media/files')

@v1_media_serve_files_bp.route('/<path:filename>', methods=['GET'])
def serve_local_file(filename):
    """
    Serve files from LOCAL_STORAGE_PATH for video rendering and media access
    """
    try:
        # Security check - prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return "Invalid file path", 400
            
        file_path = os.path.join(LOCAL_STORAGE_PATH, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return "File not found", 404
            
        # Get the file extension for MIME type detection
        _, ext = os.path.splitext(filename)
        mime_type = mimetypes.types_map.get(ext, 'application/octet-stream')
        
        # Set appropriate MIME types for media files
        if ext == '.mp4':
            mime_type = 'video/mp4'
        elif ext == '.mp3':
            mime_type = 'audio/mpeg'
        elif ext == '.wav':
            mime_type = 'audio/wav'
        elif ext == '.webm':
            mime_type = 'video/webm'
            
        response = send_from_directory(LOCAL_STORAGE_PATH, filename)
        response.headers['Content-Type'] = mime_type
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Cache-Control'] = 'no-cache'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error serving file {filename}: {str(e)}")
        return str(e), 500
