# Copyright (c) 2025 Stephen G. Pope
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

from flask import Blueprint
from app_utils import queue_task_wrapper
import logging
from services.authentication import authenticate
from services.v1.video.short.short_video_music import (
    get_available_music_tags,
    get_music_by_mood,
    get_music_by_tempo,
    get_music_recommendations
)

v1_video_short_music_bp = Blueprint('v1_video_short_music', __name__)
logger = logging.getLogger(__name__)

@v1_video_short_music_bp.route('/v1/video/short/music-tags', methods=['GET'])
@authenticate
@queue_task_wrapper(bypass_queue=True)
def get_music_tags(job_id, data):
    """Get available music tags/moods for short videos."""
    try:
        music_tags = get_available_music_tags()
        logger.info(f"Job {job_id}: Successfully retrieved {len(music_tags)} music tags")
        return music_tags, "/v1/video/short/music-tags", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Error retrieving music tags: {str(e)}", exc_info=True)
        return str(e), "/v1/video/short/music-tags", 500

@v1_video_short_music_bp.route('/v1/video/short/music-by-mood/<mood>', methods=['GET'])
@authenticate
@queue_task_wrapper(bypass_queue=True)
def get_music_by_mood_endpoint(job_id, data, mood):
    """Get music tags filtered by mood."""
    try:
        music_tags = get_music_by_mood(mood)
        logger.info(f"Job {job_id}: Successfully retrieved {len(music_tags)} music tags for mood '{mood}'")
        return music_tags, f"/v1/video/short/music-by-mood/{mood}", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Error retrieving music by mood: {str(e)}", exc_info=True)
        return str(e), f"/v1/video/short/music-by-mood/{mood}", 500

@v1_video_short_music_bp.route('/v1/video/short/music-by-tempo/<tempo>', methods=['GET'])
@authenticate
@queue_task_wrapper(bypass_queue=True)
def get_music_by_tempo_endpoint(job_id, data, tempo):
    """Get music tags filtered by tempo."""
    try:
        music_tags = get_music_by_tempo(tempo)
        logger.info(f"Job {job_id}: Successfully retrieved {len(music_tags)} music tags for tempo '{tempo}'")
        return music_tags, f"/v1/video/short/music-by-tempo/{tempo}", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Error retrieving music by tempo: {str(e)}", exc_info=True)
        return str(e), f"/v1/video/short/music-by-tempo/{tempo}", 500

@v1_video_short_music_bp.route('/v1/video/short/music-recommendations/<content_type>', methods=['GET'])
@authenticate
@queue_task_wrapper(bypass_queue=True)
def get_music_recommendations_endpoint(job_id, data, content_type):
    """Get music recommendations based on content type."""
    try:
        recommendations = get_music_recommendations(content_type)
        logger.info(f"Job {job_id}: Successfully retrieved {len(recommendations)} music recommendations for content type '{content_type}'")
        return recommendations, f"/v1/video/short/music-recommendations/{content_type}", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error retrieving music tags: {str(e)}")
        return str(e), "/v1/video/short/music-tags", 500
