from flask import Blueprint, request, jsonify
from services.simone.processor import process_video_to_blog, process_video_with_enhanced_features
from services.authentication import authenticate
from app_utils import queue_task_wrapper, validate_payload
import os
import logging

simone_bp = Blueprint('simone_bp', __name__)

# Get Tesseract path from environment or a default
# This should ideally be configured via app config or passed securely
TESSERACT_CMD_PATH = os.environ.get("TESSERACT_CMD_PATH", "/usr/bin/tesseract")

@simone_bp.route('/v1/simone/process_video', methods=['POST'])
@authenticate
@queue_task_wrapper(bypass_queue=False)
def process_video_endpoint(job_id, data):
    try:
        video_url = data.get('video_url')
        cookies_content = data.get('cookies_content')
        cookies_url = data.get('cookies_url')
        platform = data.get('platform') # Get the new platform parameter
        if not video_url:
            return {"error": "Missing 'video_url' in request data"}, "/v1/simone/process_video", 400

        logging.info(f"Processing video {video_url} for job {job_id}")

        result = process_video_to_blog(video_url, TESSERACT_CMD_PATH, platform, cookies_content, cookies_url)

        return result, "/v1/simone/process_video", 200

    except Exception as e:
        logging.error(f"Error processing video for job {job_id}: {str(e)}", exc_info=True)
        return {"error": str(e)}, "/v1/simone/process_video", 500


@simone_bp.route('/v1/simone/process_video_enhanced', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "cookies_content": {"type": "string"},
        "cookies_url": {"type": "string"},
        "include_topics": {"type": "boolean"},
        "include_x_thread": {"type": "boolean"},
        "platforms": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 10
        },
        "thread_config": {
            "type": "object",
            "properties": {
                "max_posts": {"type": "integer", "minimum": 2, "maximum": 15},
                "character_limit": {"type": "integer", "minimum": 100, "maximum": 500},
                "thread_style": {
                    "type": "string",
                    "enum": ["viral", "educational", "storytelling", "professional", "conversational"]
                }
            },
            "additionalProperties": False
        },
        "topic_config": {
            "type": "object",
            "properties": {
                "min_topics": {"type": "integer", "minimum": 1, "maximum": 5},
                "max_topics": {"type": "integer", "minimum": 3, "maximum": 15}
            },
            "additionalProperties": False
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def process_video_enhanced_endpoint(job_id, data):
    """Enhanced video processing with topic identification and X thread generation."""
    try:
        video_url = data.get('video_url')
        cookies_content = data.get('cookies_content')
        cookies_url = data.get('cookies_url')
        include_topics = data.get('include_topics', True)
        include_x_thread = data.get('include_x_thread', True)
        platforms = data.get('platforms', ['x', 'linkedin', 'instagram'])
        
        # Thread configuration
        thread_config = data.get('thread_config', {})
        default_thread_config = {
            'max_posts': 8,
            'character_limit': 280,
            'thread_style': 'viral'
        }
        thread_config = {**default_thread_config, **thread_config}
        
        # Topic configuration
        topic_config = data.get('topic_config', {})
        if topic_config:
            thread_config.update(topic_config)
        
        logging.info(f"Enhanced processing video {video_url} for job {job_id}")
        logging.info(f"Config - Topics: {include_topics}, Thread: {include_x_thread}, Platforms: {platforms}")

        result = process_video_with_enhanced_features(
            url=video_url,
            tesseract_path=TESSERACT_CMD_PATH,
            include_topics=include_topics,
            include_x_thread=include_x_thread,
            platforms=platforms,
            thread_config=thread_config,
            cookies_content=cookies_content,
            cookies_url=cookies_url
        )

        return result, "/v1/simone/process_video_enhanced", 200

    except Exception as e:
        logging.error(f"Error in enhanced video processing for job {job_id}: {str(e)}", exc_info=True)
        return {"error": str(e)}, "/v1/simone/process_video_enhanced", 500


# Direct /v1/generate_topics endpoint (alias for simone version)
@simone_bp.route('/v1/generate_topics', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "transcription_text": {"type": "string"},
        "transcription_file_url": {"type": "string", "format": "uri"},
        "min_topics": {"type": "integer", "minimum": 1, "maximum": 5},
        "max_topics": {"type": "integer", "minimum": 3, "maximum": 15},
        "include_timestamps": {"type": "boolean"},
        "cookies_content": {"type": "string"},
        "cookies_url": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def generate_topics_direct_endpoint(job_id, data):
    """Generate viral topics from transcription text (direct endpoint)."""
    try:
        import tempfile
        from services.simone.utils.social_media_generator import SocialMediaGenerator
        import os
        
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            return {"error": "OpenAI API key not configured"}, "/v1/generate_topics", 500
        
        transcription_text = data.get('transcription_text')
        transcription_file_url = data.get('transcription_file_url')
        cookies_content = data.get('cookies_content')
        cookies_url = data.get('cookies_url')
        min_topics = data.get('min_topics', 3)
        max_topics = data.get('max_topics', 8)
        include_timestamps = data.get('include_timestamps', False)
        
        if not transcription_text and not transcription_file_url:
            return {"error": "Either transcription_text or transcription_file_url is required"}, "/v1/generate_topics", 400
        
        # Create temporary file for transcription
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            if transcription_text:
                temp_file.write(transcription_text)
            else:
                # Download transcription from URL
                import requests
                response = requests.get(transcription_file_url)
                response.raise_for_status()
                temp_file.write(response.text)
            
            temp_filename = temp_file.name
        
        try:
            logging.info(f"Generating topics for job {job_id}")
            
            generator = SocialMediaGenerator(openai_api_key, temp_filename)
            topics = generator.identify_topics(
                min_topics=min_topics,
                max_topics=max_topics,
                include_timestamps=include_timestamps
            )
            
            return {
                "topics": topics,
                "job_id": job_id,
                "parameters": {
                    "min_topics": min_topics,
                    "max_topics": max_topics,
                    "include_timestamps": include_timestamps
                }
            }, "/v1/generate_topics", 200
            
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    except Exception as e:
        logging.error(f"Error generating topics for job {job_id}: {str(e)}", exc_info=True)
        return {"error": str(e)}, "/v1/generate_topics", 500


@simone_bp.route('/v1/simone/generate_topics', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "transcription_text": {"type": "string"},
        "transcription_file_url": {"type": "string", "format": "uri"},
        "cookies_content": {"type": "string"},
        "cookies_url": {"type": "string"},
        "min_topics": {"type": "integer", "minimum": 1, "maximum": 5},
        "max_topics": {"type": "integer", "minimum": 3, "maximum": 15},
        "include_timestamps": {"type": "boolean"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def generate_topics_endpoint(job_id, data):
    """Generate viral topics from transcription text."""
    try:
        import tempfile
        from services.simone.utils.social_media_generator import SocialMediaGenerator
        import os
        
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            return {"error": "OpenAI API key not configured"}, "/v1/simone/generate_topics", 500
        
        transcription_text = data.get('transcription_text')
        transcription_file_url = data.get('transcription_file_url')
        cookies_content = data.get('cookies_content')
        cookies_url = data.get('cookies_url')
        min_topics = data.get('min_topics', 3)
        max_topics = data.get('max_topics', 8)
        include_timestamps = data.get('include_timestamps', False)
        
        if not transcription_text and not transcription_file_url:
            return {"error": "Either transcription_text or transcription_file_url is required"}, "/v1/simone/generate_topics", 400
        
        # Create temporary file for transcription
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            if transcription_text:
                temp_file.write(transcription_text)
            else:
                # Download transcription from URL
                import requests
                response = requests.get(transcription_file_url)
                response.raise_for_status()
                temp_file.write(response.text)
            
            temp_filename = temp_file.name
        
        try:
            logging.info(f"Generating topics for job {job_id}")
            
            generator = SocialMediaGenerator(openai_api_key, temp_filename)
            topics = generator.identify_topics(
                min_topics=min_topics,
                max_topics=max_topics,
                include_timestamps=include_timestamps
            )
            
            return {
                "topics": topics,
                "job_id": job_id,
                "parameters": {
                    "min_topics": min_topics,
                    "max_topics": max_topics,
                    "include_timestamps": include_timestamps
                }
            }, "/v1/simone/generate_topics", 200
            
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    except Exception as e:
        logging.error(f"Error generating topics for job {job_id}: {str(e)}", exc_info=True)
        return {"error": str(e)}, "/v1/simone/generate_topics", 500


@simone_bp.route('/v1/simone/generate_x_thread', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "transcription_text": {"type": "string"},
        "transcription_file_url": {"type": "string", "format": "uri"},
        "cookies_content": {"type": "string"},
        "cookies_url": {"type": "string"},
        "max_posts": {"type": "integer", "minimum": 2, "maximum": 15},
        "character_limit": {"type": "integer", "minimum": 100, "maximum": 500},
        "thread_style": {
            "type": "string",
            "enum": ["viral", "educational", "storytelling", "professional", "conversational"]
        },
        "topic_focus": {"type": "string"},
        "include_timestamps": {"type": "boolean"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def generate_x_thread_endpoint(job_id, data):
    """Generate X/Twitter thread from transcription."""
    try:
        import tempfile
        from services.simone.utils.social_media_generator import SocialMediaGenerator
        import os
        
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            return {"error": "OpenAI API key not configured"}, "/v1/simone/generate_x_thread", 500
        
        transcription_text = data.get('transcription_text')
        transcription_file_url = data.get('transcription_file_url')
        cookies_content = data.get('cookies_content')
        cookies_url = data.get('cookies_url')
        max_posts = data.get('max_posts', 8)
        character_limit = data.get('character_limit', 280)
        thread_style = data.get('thread_style', 'viral')
        topic_focus = data.get('topic_focus')
        include_timestamps = data.get('include_timestamps', False)
        
        if not transcription_text and not transcription_file_url:
            return {"error": "Either transcription_text or transcription_file_url is required"}, "/v1/simone/generate_x_thread", 400
        
        # Create temporary file for transcription
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            if transcription_text:
                temp_file.write(transcription_text)
            else:
                # Download transcription from URL
                import requests
                response = requests.get(transcription_file_url)
                response.raise_for_status()
                temp_file.write(response.text)
            
            temp_filename = temp_file.name
        
        try:
            logging.info(f"Generating X thread for job {job_id}")
            
            generator = SocialMediaGenerator(openai_api_key, temp_filename)
            thread = generator.generate_x_thread(
                max_posts=max_posts,
                character_limit=character_limit,
                thread_style=thread_style,
                include_timestamps=include_timestamps,
                topic_focus=topic_focus
            )
            
            return {
                "thread": thread,
                "job_id": job_id,
                "parameters": {
                    "max_posts": max_posts,
                    "character_limit": character_limit,
                    "thread_style": thread_style,
                    "topic_focus": topic_focus,
                    "include_timestamps": include_timestamps
                }
            }, "/v1/simone/generate_x_thread", 200
            
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    except Exception as e:
        logging.error(f"Error generating X thread for job {job_id}: {str(e)}", exc_info=True)
        return {"error": str(e)}, "/v1/simone/generate_x_thread", 500
