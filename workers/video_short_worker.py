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

import logging
from services.cloud_storage import upload_file
from services.v1.video.short.short_video_create import create_short_video as process_short_video
from services.v1.video.short.short_video_status import (
    create_video_status,
    mark_video_completed,
    mark_video_failed
)

logger = logging.getLogger(__name__)

def create_short_video_worker(job_id, data):
    """
    Worker function to create short video - runs in background without authentication context.
    This function is called by RQ workers and should not have authentication decorators.
    """
    scenes = data['scenes']
    config = data.get('config', {})
    webhook_url = data.get('webhook_url')
    custom_id = data.get('id')
    
    # Use custom ID if provided, otherwise use generated job_id
    if custom_id:
        job_id = custom_id
    
    # If still no job_id, generate one
    if not job_id:
        import uuid
        job_id = str(uuid.uuid4())

    logger.info(f"Job {job_id}: Received short video creation request with {len(scenes)} scenes")

    # Create initial status entry
    user_id = getattr(data, 'user_id', 'unknown')  # This might need adjustment based on auth system
    create_video_status(job_id, user_id, len(scenes), config)

    try:
        # Process the short video creation
        output_filename = process_short_video(
            scenes=scenes,
            config=config,
            job_id=job_id
        )

        # Upload the resulting video to cloud storage
        cloud_url = upload_file(output_filename)

        logger.info(f"Job {job_id}: Short video uploaded to cloud storage: {cloud_url}")

        # Mark video as completed
        mark_video_completed(job_id, cloud_url)

        # Return the cloud URL for the uploaded video
        return cloud_url, "/v1/video/short/create", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error creating short video: {str(e)}", exc_info=True)
        
        # Mark video as failed
        mark_video_failed(job_id, str(e))
        
        return str(e), "/v1/video/short/create", 500
