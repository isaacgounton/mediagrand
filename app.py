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
from redis import Redis
from rq import Queue, Worker
from rq.job import Job
from services.webhook import send_webhook
import uuid
import os
import time
import logging
from functools import wraps
from version import BUILD_NUMBER
from app_utils import log_job_status

MAX_QUEUE_LENGTH = int(os.environ.get('MAX_QUEUE_LENGTH', 0))

def create_app():
    app = Flask(__name__)
    
    # Initialize Redis connection
    redis_conn = Redis(host='redis', port=6379)
    task_queue = Queue('tasks', connection=redis_conn)
    
    # Log at startup
    logging.info(f"Worker {os.getpid()} starting with Redis queue")

    def process_task(job_id, data, task_func, start_time):
        """Worker function to process tasks"""
        worker_pid = os.getpid()
        run_start_time = time.time()
        queue_time = time.time() - start_time
        
        try:
            # Log job status as running
            log_job_status(job_id, {
                "job_status": "running",
                "job_id": job_id,
                "process_id": worker_pid,
                "response": None
            })
            
            logging.info(f"Worker {worker_pid}: Executing task for job {job_id}")
            response = task_func()
            logging.info(f"Worker {worker_pid}: Task completed for job {job_id}")
            
            run_time = time.time() - run_start_time
            total_time = time.time() - start_time

            response_data = {
                "endpoint": response[1],
                "code": response[2],
                "id": data.get("id"),
                "job_id": job_id,
                "response": response[0] if response[2] == 200 else None,
                "message": "success" if response[2] == 200 else response[0],
                "pid": worker_pid,
                "run_time": round(run_time, 3),
                "queue_time": round(queue_time, 3),
                "total_time": round(total_time, 3),
                "queue_length": len(task_queue),
                "build_number": BUILD_NUMBER
            }
            
            # Log job status as done
            log_job_status(job_id, {
                "job_status": "done",
                "job_id": job_id,
                "process_id": worker_pid,
                "response": response_data
            })

            # Send webhook if URL provided
            if data.get("webhook_url"):
                send_webhook(data.get("webhook_url"), response_data)

            return response_data
            
        except Exception as e:
            logging.error(f"Worker {worker_pid}: Error processing job {job_id}: {str(e)}", exc_info=True)
            raise

    # Decorator to add tasks to the queue or bypass it
    def queue_task(bypass_queue=False):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                job_id = str(uuid.uuid4())
                data = request.json if request.is_json else {}
                pid = os.getpid()
                start_time = time.time()
                
                if bypass_queue or 'webhook_url' not in data:
                    # Execute task immediately
                    log_job_status(job_id, {
                        "job_status": "running",
                        "job_id": job_id,
                        "process_id": pid,
                        "response": None
                    })
                    
                    response = f(job_id=job_id, data=data, *args, **kwargs)
                    run_time = time.time() - start_time

                    if isinstance(response, tuple) and len(response) == 3:
                        response_obj = {
                            "code": response[2],
                            "id": data.get("id"),
                            "job_id": job_id,
                            "response": response[0] if response[2] == 200 else None,
                            "message": "success" if response[2] == 200 else response[0],
                            "run_time": round(run_time, 3),
                            "queue_time": 0,
                            "total_time": round(run_time, 3),
                            "pid": pid,
                            "queue_length": len(task_queue),
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
                    # Check queue length limit
                    if MAX_QUEUE_LENGTH > 0 and len(task_queue) >= MAX_QUEUE_LENGTH:
                        error_response = {
                            "code": 429,
                            "id": data.get("id"),
                            "job_id": job_id,
                            "message": f"MAX_QUEUE_LENGTH ({MAX_QUEUE_LENGTH}) reached",
                            "pid": pid,
                            "queue_length": len(task_queue),
                            "build_number": BUILD_NUMBER
                        }
                        
                        log_job_status(job_id, {
                            "job_status": "rejected",
                            "job_id": job_id,
                            "process_id": pid,
                            "response": error_response
                        })
                        
                        return error_response, 429
                    
                    # Queue the task
                    log_job_status(job_id, {
                        "job_status": "queued",
                        "job_id": job_id,
                        "process_id": pid,
                        "response": None
                    })
                    
                    task_func = lambda: f(job_id=job_id, data=data, *args, **kwargs)
                    job = task_queue.enqueue(
                        process_task,
                        args=(job_id, data, task_func, start_time),
                        job_id=job_id,
                        job_timeout='1h'
                    )
                    
                    return {
                        "code": 202,
                        "id": data.get("id"),
                        "job_id": job_id,
                        "message": "processing",
                        "pid": pid,
                        "max_queue_length": MAX_QUEUE_LENGTH if MAX_QUEUE_LENGTH > 0 else "unlimited",
                        "queue_length": len(task_queue),
                        "build_number": BUILD_NUMBER
                    }, 202
            return wrapper
        return decorator

    app.queue_task = queue_task

    # Create RQ worker in a separate process
    Worker(['tasks'], connection=redis_conn).work(with_scheduler=True)

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
    from routes.v1.video.short.short_video_create import v1_video_short_create_bp
    from routes.v1.video.short.short_video_status import v1_video_short_status_bp
    from routes.v1.video.short.music import music_bp
    from routes.v1.media.serve_files import v1_media_serve_files_bp

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
    app.register_blueprint(v1_video_short_create_bp)
    app.register_blueprint(v1_video_short_status_bp)
    app.register_blueprint(music_bp, url_prefix='/v1/video/short/music')
    app.register_blueprint(v1_media_serve_files_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
