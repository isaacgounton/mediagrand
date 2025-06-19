# Copyright (c) 2025 Isaac Gounton
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from flask import Flask, request
from flask_cors import CORS
from redis import Redis
from rq import Queue, Worker
from rq.job import Job
from services.webhook import send_webhook
import uuid
import os
import time
import logging
from functools import wraps
import importlib
from version import BUILD_NUMBER
from app_utils import log_job_status # Assuming log_job_status is here

def create_redis_connection(max_retries=5, retry_delay=2):
    """Create Redis connection with retry logic"""
    redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
    
    for attempt in range(max_retries):
        try:
            redis_conn = Redis.from_url(
                redis_url,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test the connection
            redis_conn.ping()
            logging.info(f"Successfully connected to Redis at {redis_url}")
            return redis_conn
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Could not connect to Redis instance: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
            else:
                logging.error(f"Failed to connect to Redis after {max_retries} attempts: {str(e)}")
                raise

# Global RQ and Redis setup
redis_conn = create_redis_connection()
task_queue = Queue(
    'tasks',
    connection=redis_conn,
    default_timeout='1h'
)

MAX_QUEUE_LENGTH = int(os.environ.get('MAX_QUEUE_LENGTH', 0))

class TaskWrapper:
    """Wrapper class to make task functions pickleable by storing their path."""
    def __init__(self, func_path, job_id, data):
        self.func_path = func_path
        self.job_id = job_id
        self.data = data

    def __call__(self):
        # Dynamically import and execute the function
        try:
            module_path, func_name = self.func_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            actual_func = getattr(module, func_name)
            return actual_func(job_id=self.job_id, data=self.data)
        except Exception as e:
            logging.error(f"TaskWrapper: Error importing/calling {self.func_path} for job {self.job_id}: {str(e)}", exc_info=True)
            raise # Re-raise to be caught by process_task's try-except

# This function will be run by RQ workers
def process_task(task_wrapper_instance, start_time):
    """Worker function to process tasks"""
    worker_pid = os.getpid()
    run_start_time = time.time()
    queue_time = time.time() - start_time
    
    try:
        log_job_status(task_wrapper_instance.job_id, {
            "job_status": "running",
            "job_id": task_wrapper_instance.job_id,
            "process_id": worker_pid,
            "response": None
        })
        
        logging.info(f"Worker {worker_pid}: Executing task for job {task_wrapper_instance.job_id}")
        response = task_wrapper_instance() # Calls TaskWrapper.__call__
        logging.info(f"Worker {worker_pid}: Task completed for job {task_wrapper_instance.job_id}")
        
        run_time = time.time() - run_start_time
        total_time = time.time() - start_time

        response_data = {
            "endpoint": response[1],
            "code": response[2],
            "id": task_wrapper_instance.data.get("id"),
            "job_id": task_wrapper_instance.job_id,
            "response": response[0] if response[2] == 200 else None,
            "message": "success" if response[2] == 200 else response[0],
            "pid": worker_pid,
            "run_time": round(run_time, 3),
            "queue_time": round(queue_time, 3),
            "total_time": round(total_time, 3),
            "queue_length": len(task_queue), # Uses global task_queue
            "build_number": BUILD_NUMBER
        }
        
        log_job_status(task_wrapper_instance.job_id, {
            "job_status": "done",
            "job_id": task_wrapper_instance.job_id,
            "process_id": worker_pid,
            "response": response_data
        })

        if task_wrapper_instance.data.get("webhook_url"):
            send_webhook(task_wrapper_instance.data.get("webhook_url"), response_data)

        return response_data
        
    except Exception as e:
        logging.error(f"Worker {worker_pid}: Error processing job {task_wrapper_instance.job_id}: {str(e)}", exc_info=True)
        log_job_status(task_wrapper_instance.job_id, {
            "job_status": "failed",
            "job_id": task_wrapper_instance.job_id,
            "process_id": worker_pid,
            "error": str(e)
        })
        raise

def queue_task(bypass_queue=False):
    def decorator(f): 
        @wraps(f)
        def wrapper(*args, **kwargs):
            job_id = str(uuid.uuid4())
            current_request_data = getattr(request, '_validated_json', 
                                           request.json if request.is_json else {})
            pid = os.getpid()
            start_time = time.time()
            
            if bypass_queue or 'webhook_url' not in current_request_data:
                log_job_status(job_id, {
                    "job_status": "running",
                    "job_id": job_id,
                    "process_id": pid,
                    "response": None
                })
                response = f(job_id=job_id, data=current_request_data, *args, **kwargs)
                run_time = time.time() - start_time
                if isinstance(response, tuple) and len(response) == 3:
                    response_obj = {
                        "code": response[2],
                        "id": current_request_data.get("id"),
                        "job_id": job_id,
                        "response": response[0] if response[2] == 200 else None,
                        "message": "success" if response[2] == 200 else response[0],
                        "run_time": round(run_time, 3),
                        "queue_time": 0,
                        "total_time": round(run_time, 3),
                        "pid": pid,
                        "queue_length": len(task_queue), # Uses global task_queue
                        "build_number": BUILD_NUMBER
                    }
                    log_job_status(job_id, {
                        "job_status": "done",
                        "job_id": job_id,
                        "process_id": pid,
                        "response": response_obj
                    })
                    return response_obj, response[2]
                return response
            else:
                if MAX_QUEUE_LENGTH > 0 and len(task_queue) >= MAX_QUEUE_LENGTH: # Uses global task_queue
                    error_response = {
                        "code": 429,
                        "id": current_request_data.get("id"),
                        "job_id": job_id,
                        "message": f"MAX_QUEUE_LENGTH ({MAX_QUEUE_LENGTH}) reached",
                        "pid": pid,
                        "queue_length": len(task_queue), # Uses global task_queue
                        "build_number": BUILD_NUMBER
                    }
                    log_job_status(job_id, {
                        "job_status": "rejected",
                        "job_id": job_id,
                        "process_id": pid,
                        "response": error_response
                    })
                    return error_response, 429
                
                log_job_status(job_id, {
                    "job_status": "queued",
                    "job_id": job_id,
                    "process_id": pid,
                    "response": None
                })
                
                func_path = f"{f.__module__}.{f.__name__}"
                task_wrapper_obj = TaskWrapper(func_path, job_id, current_request_data)
                
                job = task_queue.enqueue( # Uses global task_queue
                    'app.process_task', # Target is the global process_task, referenced by its import path
                    args=(task_wrapper_obj, start_time),
                    job_id=job_id,
                    job_timeout='1h'
                )
                
                return {
                    "code": 202,
                    "id": current_request_data.get("id"),
                    "job_id": job_id,
                    "message": "processing",
                    "pid": pid,
                    "max_queue_length": MAX_QUEUE_LENGTH if MAX_QUEUE_LENGTH > 0 else "unlimited",
                    "queue_length": len(task_queue), # Uses global task_queue
                    "build_number": BUILD_NUMBER
                }, 202
        return wrapper
    return decorator

def create_app():
    app = Flask(__name__)
    
    # Configure CORS to allow requests from localhost:3000 and the shorts domain
    CORS(app, resources={
        r"/*": {
            "origins": [
                "http://localhost:3000",
                "https://shorts.dahopevi.com",
                "http://shorts.dahopevi.com",
                "http://localhost:*",
                "https://localhost:*"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
            "supports_credentials": True
        }
    })
    
    # redis_url, redis_conn, and task_queue are now global
    
    logging.info(f"Flask app {os.getpid()} starting, using global Redis queue")

    # Attach the queue_task decorator (which is now global) to the app instance
    # The decorator itself will use the global task_queue
    app.queue_task = queue_task

    # Import blueprints
    from routes.media_to_mp3 import convert_bp
    from routes.transcribe_media import transcribe_bp
    from routes.combine_videos import combine_bp
    from routes.audio_mixing import audio_mixing_bp
    from routes.gdrive_upload import gdrive_upload_bp
    from routes.authenticate import auth_bp
    from routes.caption_video import caption_bp 
    from routes.extract_keyframes import extract_keyframes_bp
    from routes.image_to_video import image_to_video_bp
    from routes.health import health_bp
    

    # Register blueprints
    app.register_blueprint(convert_bp)
    app.register_blueprint(transcribe_bp)
    app.register_blueprint(combine_bp)
    app.register_blueprint(audio_mixing_bp)
    app.register_blueprint(gdrive_upload_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(caption_bp)
    app.register_blueprint(extract_keyframes_bp)
    app.register_blueprint(image_to_video_bp)
    app.register_blueprint(health_bp)
    
    

    # version 1.0
    from routes.v1.ffmpeg.ffmpeg_compose import v1_ffmpeg_compose_bp
    from routes.v1.media.media_transcribe import v1_media_transcribe_bp
    from routes.v1.media.feedback import v1_media_feedback_bp
    from routes.v1.media.convert.media_to_mp3 import v1_media_convert_mp3_bp
    from routes.v1.video.concatenate import v1_video_concatenate_bp
    from routes.v1.video.caption_video import v1_video_caption_bp
    from routes.v1.image.convert.image_to_video import v1_image_convert_video_bp
    from routes.v1.toolkit.test import v1_toolkit_test_bp
    from routes.v1.toolkit.authenticate import v1_toolkit_auth_bp
    from routes.v1.code.execute.execute_python import v1_code_execute_bp
    from routes.v1.s3.upload import v1_s3_upload_bp
    from routes.v1.video.thumbnail import v1_video_thumbnail_bp
    from routes.v1.media.download import v1_media_download_bp
    from routes.v1.media.convert.media_convert import v1_media_convert_bp
    from routes.v1.audio.concatenate import v1_audio_concatenate_bp
    from routes.v1.media.silence import v1_media_silence_bp
    from routes.v1.video.cut import v1_video_cut_bp
    from routes.v1.video.split import v1_video_split_bp
    from routes.v1.video.trim import v1_video_trim_bp
    from routes.v1.media.metadata import v1_media_metadata_bp
    from routes.v1.toolkit.job_status import v1_toolkit_job_status_bp
    from routes.v1.toolkit.jobs_status import v1_toolkit_jobs_status_bp
    from routes.v1.audio.speech import v1_audio_speech_bp
    from routes.v1.media.media_duration import v1_media_duration_bp
    from routes.v1.media.serve_files import v1_media_serve_files_bp
    from routes.v1.image.convert.image_convert import v1_image_convert_bp
    from routes.v1.audio.convert.audio_convert import v1_audio_convert_bp
    from routes.v1.video.merge import v1_video_merge_bp
    from routes.v1.video.extract_frame import v1_video_extract_frame_bp
    from routes.v1.video.tts_captioned_video import v1_video_tts_captioned_bp

    app.register_blueprint(v1_ffmpeg_compose_bp)
    app.register_blueprint(v1_media_transcribe_bp)
    app.register_blueprint(v1_media_feedback_bp)
    
    # Register a special route for Next.js root asset paths
    from routes.v1.media.feedback import create_root_next_routes
    create_root_next_routes(app)
    
    app.register_blueprint(v1_media_convert_mp3_bp)
    app.register_blueprint(v1_video_concatenate_bp)
    app.register_blueprint(v1_video_caption_bp)
    app.register_blueprint(v1_image_convert_video_bp)
    app.register_blueprint(v1_toolkit_test_bp)
    app.register_blueprint(v1_toolkit_auth_bp)
    app.register_blueprint(v1_code_execute_bp)
    app.register_blueprint(v1_s3_upload_bp)
    app.register_blueprint(v1_video_thumbnail_bp)
    app.register_blueprint(v1_media_download_bp)
    app.register_blueprint(v1_media_convert_bp)
    app.register_blueprint(v1_audio_concatenate_bp)
    app.register_blueprint(v1_media_silence_bp)
    app.register_blueprint(v1_video_cut_bp)
    app.register_blueprint(v1_video_split_bp)
    app.register_blueprint(v1_video_trim_bp)
    app.register_blueprint(v1_media_metadata_bp)
    app.register_blueprint(v1_toolkit_job_status_bp)
    app.register_blueprint(v1_toolkit_jobs_status_bp)
    app.register_blueprint(v1_audio_speech_bp)
    app.register_blueprint(v1_media_duration_bp)
    app.register_blueprint(v1_media_serve_files_bp)
    app.register_blueprint(v1_image_convert_bp)
    app.register_blueprint(v1_audio_convert_bp)
    app.register_blueprint(v1_video_merge_bp)
    app.register_blueprint(v1_video_extract_frame_bp)
    app.register_blueprint(v1_video_tts_captioned_bp)

    # Add homepage route
    @app.route('/')
    def homepage():
        """Homepage showing API information and available endpoints"""
        return {
            "message": "DahoPevi API",
            "version": "1.0.0",
            "build": BUILD_NUMBER,
            "status": "healthy",
            "description": "DahoPevi - Video & Audio Processing API",
            "documentation": {
                "url": "/docs",
                "description": "API documentation and endpoints"
            },
            "endpoints": {
                "v1": {
                    "media": {
                        "transcribe": "/v1/media/transcribe",
                        "convert": "/v1/media/convert", 
                        "download": "/v1/media/download",
                        "metadata": "/v1/media/metadata",
                        "duration": "/v1/media/duration",
                        "silence": "/v1/media/silence",
                        "serve_files": "/v1/media/serve_files"
                    },
                    "video": {
                        "concatenate": "/v1/video/concatenate",
                        "caption": "/v1/video/caption",
                        "thumbnail": "/v1/video/thumbnail",
                        "cut": "/v1/video/cut",
                        "split": "/v1/video/split",
                        "trim": "/v1/video/trim",
                        "merge": "/v1/video/merge",
                        "extract_frame": "/v1/video/extract-frame",
                        "tts_captioned": "/v1/video/tts-captioned"
                    },
                    "audio": {
                        "concatenate": "/v1/audio/concatenate",
                        "speech": "/v1/audio/speech",
                        "convert": "/v1/audio/convert"
                    },
                    "image": {
                        "convert_to_video": "/v1/image/convert/video",
                        "convert": "/v1/image/convert"
                    },
                    "toolkit": {
                        "test": "/v1/toolkit/test",
                        "authenticate": "/v1/toolkit/authenticate",
                        "job_status": "/v1/toolkit/job_status",
                        "jobs_status": "/v1/toolkit/jobs_status"
                    },
                    "code": {
                        "execute_python": "/v1/code/execute/python"
                    },
                    "s3": {
                        "upload": "/v1/s3/upload"
                    },
                    "ffmpeg": {
                        "compose": "/v1/ffmpeg/compose"
                    }
                },
                "legacy": {
                    "transcribe": "/transcribe",
                    "convert": "/convert", 
                    "combine": "/combine",
                    "audio_mixing": "/audio_mixing",
                    "gdrive_upload": "/gdrive_upload",
                    "authenticate": "/authenticate",
                    "caption": "/caption",
                    "extract_keyframes": "/extract_keyframes",
                    "image_to_video": "/image_to_video",
                    "health": "/health"
                }
            }
        }

    # Add docs route
    @app.route('/docs')
    def docs():
        """API documentation route"""
        return {
            "title": "DahoPevi API Documentation",
            "version": "1.0.0",
            "build": BUILD_NUMBER,
            "description": "Comprehensive video and audio processing API with transcription, conversion, and manipulation capabilities.",
            "features": [
                "Audio/Video Transcription with Whisper AI",
                "Media Format Conversion",
                "Video Concatenation and Editing",
                "Video Merging with Background Music",
                "Frame Extraction from Videos",
                "TTS Captioned Video Generation",
                "Image to Video Conversion",
                "Text-to-Speech Generation",
                "Cloud Storage Integration",
                "Asynchronous Processing with Webhooks"
            ],
            "authentication": {
                "method": "API Key",
                "header": "x-api-key",
                "description": "Include your API key in the x-api-key header"
            },
            "endpoints_documentation": "Visit individual endpoint URLs with OPTIONS method for detailed documentation",
            "examples": {
                "transcribe_media": {
                    "url": "/v1/media/transcribe",
                    "method": "POST",
                    "description": "Transcribe audio/video to text with enhanced non-English language support"
                },
                "convert_media": {
                    "url": "/v1/media/convert",
                    "method": "POST", 
                    "description": "Convert media between different formats"
                }
            },
            "support": {
                "github": "https://github.com/isaacgounton/dahopevi",
                "contact": "isaac@etugrand.com"
            }
        }

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
