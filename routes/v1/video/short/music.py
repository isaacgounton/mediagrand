import os
from flask import Blueprint, request, jsonify
from services.v1.video.short.short_video_music import MusicManager
from werkzeug.utils import secure_filename
from typing import List, Dict, Optional

music_bp = Blueprint('music', __name__)
music_manager = MusicManager()

@music_bp.route('/moods', methods=['GET'])
def list_moods():
    """List all available music moods."""
    try:
        moods = music_manager.list_available_moods()
        return jsonify({"moods": moods}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@music_bp.route('/upload', methods=['POST'])
def upload_music():
    """Upload a new music track with mood categorization."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    mood = request.form.get('mood')
    if not mood:
        return jsonify({"error": "Mood category required"}), 400
    
    if mood not in music_manager.list_available_moods():
        return jsonify({"error": f"Invalid mood. Available moods: {', '.join(music_manager.list_available_moods())}"}), 400
    
    try:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', filename)
        file.save(temp_path)
        
        # Add to music library
        final_path = music_manager.add_music_file(temp_path, mood)
        
        # Get file duration using ffmpeg
        import ffmpeg
        probe = ffmpeg.probe(final_path)
        duration = float(probe['streams'][0]['duration'])
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Generate public URL (you'll need to implement get_public_url based on your storage setup)
        public_url = f"/music/{os.path.basename(final_path)}"
        
        return jsonify({
            "id": f"music_{os.path.splitext(filename)[0]}",
            "name": filename,
            "mood": mood,
            "duration": duration,
            "url": public_url
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@music_bp.route('/<mood>', methods=['GET'])
def get_music_by_mood(mood: str):
    """Get list of music tracks for a specific mood."""
    if mood not in music_manager.list_available_moods():
        return jsonify({"error": f"Invalid mood. Available moods: {', '.join(music_manager.list_available_moods())}"}), 400
    
    try:
        # Get tracks for the specified mood
        music_path = music_manager.get_music_by_mood(mood)
        if not music_path:
            return jsonify({"tracks": []}), 200
        
        # Convert file paths to track objects
        tracks = []
        
        # Handle both single path and list of paths
        paths = [music_path] if isinstance(music_path, str) else music_path
        
        for path in paths:
            filename = os.path.basename(path)
            name = os.path.splitext(filename)[0]
            
            # Get duration using ffmpeg
            probe = ffmpeg.probe(path)
            duration = float(probe['streams'][0]['duration'])
            
            # Generate public URL
            public_url = f"/music/{filename}"
            
            tracks.append({
                "id": f"music_{name}",
                "name": filename,
                "mood": mood,
                "duration": duration,
                "url": public_url
            })
        
        return jsonify({"tracks": tracks}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
