# filepath: e:\dev.ai\API\dahopevi\services\v1\video\short_video_status.py
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

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

# Status tracking file path
STATUS_FILE_PATH = os.path.join(LOCAL_STORAGE_PATH, "short_video_status.json")

def load_status_data() -> Dict[str, Any]:
    """Load status data from JSON file."""
    try:
        if os.path.exists(STATUS_FILE_PATH):
            with open(STATUS_FILE_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading status data: {str(e)}")
    
    return {"videos": {}}

def save_status_data(data: Dict[str, Any]) -> None:
    """Save status data to JSON file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(STATUS_FILE_PATH), exist_ok=True)
        
        with open(STATUS_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving status data: {str(e)}")

def create_video_status(job_id: str, user_id: str, scenes_count: int, config: Dict) -> Dict[str, Any]:
    """
    Create initial video status entry.
    
    Args:
        job_id: Unique job identifier
        user_id: User identifier
        scenes_count: Number of scenes in the video
        config: Video configuration
        
    Returns:
        Created status entry
    """
    data = load_status_data()
    
    status_entry = {
        "job_id": job_id,
        "user_id": user_id,
        "status": "processing",
        "progress": 0,
        "scenes_count": scenes_count,
        "current_scene": 0,
        "config": config,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "estimated_completion": None,
        "cloud_url": None,
        "error_message": None,
        "processing_stages": {
            "tts_generation": "pending",
            "video_search": "pending",
            "caption_generation": "pending",
            "video_rendering": "pending",
            "upload": "pending"
        }
    }
    
    data["videos"][job_id] = status_entry
    save_status_data(data)
    
    logger.info(f"Created video status for job {job_id}")
    return status_entry

def update_video_status(job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update video status.
    
    Args:
        job_id: Job identifier
        updates: Dictionary of fields to update
        
    Returns:
        Updated status entry or None if not found
    """
    data = load_status_data()
    
    if job_id not in data["videos"]:
        logger.warning(f"Video status not found for job {job_id}")
        return None
    
    # Update fields
    status_entry = data["videos"][job_id]
    for key, value in updates.items():
        status_entry[key] = value
    
    status_entry["updated_at"] = datetime.now().isoformat()
    
    # Calculate estimated completion if progress is provided
    if "progress" in updates and updates["progress"] > 0:
        created_time = datetime.fromisoformat(status_entry["created_at"])
        elapsed = datetime.now() - created_time
        total_estimated = elapsed * (100 / updates["progress"])
        completion_time = created_time + total_estimated
        status_entry["estimated_completion"] = completion_time.isoformat()
    
    save_status_data(data)
    
    logger.info(f"Updated video status for job {job_id}: {updates}")
    return status_entry

def get_video_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get video status by job ID.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Status entry or None if not found
    """
    data = load_status_data()
    return data["videos"].get(job_id)

def get_user_videos(user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get videos for a specific user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of videos to return
        offset: Number of videos to skip
        
    Returns:
        List of video status entries for the user
    """
    data = load_status_data()
    user_videos = []
    
    for job_id, video_status in data["videos"].items():
        if video_status.get("user_id") == user_id:
            user_videos.append(video_status)
    
    # Sort by creation date (newest first)
    user_videos.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Apply pagination
    return user_videos[offset:offset + limit]

def get_recent_videos(hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recently created videos.
    
    Args:
        hours: Number of hours to look back
        limit: Maximum number of videos to return
        
    Returns:
        List of recent video status entries
    """
    data = load_status_data()
    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_videos = []
    
    for job_id, video_status in data["videos"].items():
        try:
            created_time = datetime.fromisoformat(video_status.get("created_at", ""))
            if created_time >= cutoff_time:
                recent_videos.append(video_status)
        except Exception as e:
            logger.warning(f"Invalid created_at format for job {job_id}: {e}")
    
    # Sort by creation date (newest first)
    recent_videos.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return recent_videos[:limit]

def update_processing_stage(job_id: str, stage: str, status: str) -> Optional[Dict[str, Any]]:
    """
    Update a specific processing stage.
    
    Args:
        job_id: Job identifier
        stage: Processing stage name
        status: Stage status (pending, processing, completed, failed)
        
    Returns:
        Updated status entry or None if not found
    """
    valid_stages = ["tts_generation", "video_search", "caption_generation", "video_rendering", "upload"]
    valid_statuses = ["pending", "processing", "completed", "failed"]
    
    if stage not in valid_stages:
        logger.error(f"Invalid processing stage: {stage}")
        return None
    
    if status not in valid_statuses:
        logger.error(f"Invalid stage status: {status}")
        return None
    
    data = load_status_data()
    
    if job_id not in data["videos"]:
        logger.warning(f"Video status not found for job {job_id}")
        return None
    
    # Update the specific stage
    status_entry = data["videos"][job_id]
    status_entry["processing_stages"][stage] = status
    status_entry["updated_at"] = datetime.now().isoformat()
    
    # Calculate overall progress based on completed stages
    stages = status_entry["processing_stages"]
    completed_stages = sum(1 for s in stages.values() if s == "completed")
    total_stages = len(stages)
    progress = int((completed_stages / total_stages) * 100)
    
    status_entry["progress"] = progress
    
    # Update overall status
    if any(s == "failed" for s in stages.values()):
        status_entry["status"] = "failed"
    elif all(s == "completed" for s in stages.values()):
        status_entry["status"] = "completed"
    elif any(s == "processing" for s in stages.values()):
        status_entry["status"] = "processing"
    
    save_status_data(data)
    
    logger.info(f"Updated processing stage {stage} to {status} for job {job_id}")
    return status_entry

def mark_video_completed(job_id: str, cloud_url: str) -> Optional[Dict[str, Any]]:
    """
    Mark video as completed with cloud URL.
    
    Args:
        job_id: Job identifier
        cloud_url: URL of the uploaded video
        
    Returns:
        Updated status entry or None if not found
    """
    updates = {
        "status": "completed",
        "progress": 100,
        "cloud_url": cloud_url
    }
    
    return update_video_status(job_id, updates)

def mark_video_failed(job_id: str, error_message: str) -> Optional[Dict[str, Any]]:
    """
    Mark video as failed with error message.
    
    Args:
        job_id: Job identifier
        error_message: Error description
        
    Returns:
        Updated status entry or None if not found
    """
    updates = {
        "status": "failed",
        "error_message": error_message
    }
    
    return update_video_status(job_id, updates)

def cleanup_old_statuses(days: int = 30) -> int:
    """
    Clean up old video statuses.
    
    Args:
        days: Number of days to keep statuses
        
    Returns:
        Number of statuses cleaned up
    """
    data = load_status_data()
    cutoff_time = datetime.now() - timedelta(days=days)
    
    jobs_to_remove = []
    for job_id, video_status in data["videos"].items():
        try:
            created_time = datetime.fromisoformat(video_status.get("created_at", ""))
            if created_time < cutoff_time:
                jobs_to_remove.append(job_id)
        except Exception as e:
            logger.warning(f"Invalid created_at format for job {job_id}: {e}")
            # Remove entries with invalid timestamps
            jobs_to_remove.append(job_id)
    
    # Remove old entries
    for job_id in jobs_to_remove:
        del data["videos"][job_id]
    
    if jobs_to_remove:
        save_status_data(data)
        logger.info(f"Cleaned up {len(jobs_to_remove)} old video statuses")
    
    return len(jobs_to_remove)
