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
from flask import Blueprint, request
from config import LOCAL_STORAGE_PATH
from services.authentication import authenticate
from app_utils import queue_task_wrapper, validate_payload

v1_toolkit_job_status_bp = Blueprint('v1_toolkit_job_status', __name__)
logger = logging.getLogger(__name__)

@v1_toolkit_job_status_bp.route('/v1/toolkit/job/status', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string"
        }
    },
    "required": ["job_id"],
})
@queue_task_wrapper(bypass_queue=True)
def get_job_status(job_id, data):

    get_job_id = data.get('job_id')

    logger.info(f"Retrieving status for job {get_job_id}")
    
    try:
        # Construct the path to the job status file
        job_file_path = os.path.join(LOCAL_STORAGE_PATH, 'jobs', f"{get_job_id}.json")
        logger.info(f"Looking for job file at: {job_file_path}")
        
        # Check if the job file exists
        if not os.path.exists(job_file_path):
            # Log available files for debugging
            jobs_dir = os.path.join(LOCAL_STORAGE_PATH, 'jobs')
            if os.path.exists(jobs_dir):
                available_files = os.listdir(jobs_dir)
                logger.info(f"Available job files: {available_files}")
            else:
                logger.warning(f"Jobs directory does not exist: {jobs_dir}")
            return {"error": "Job not found", "job_id": get_job_id}, "/v1/toolkit/job/status", 404
        
        # Read the job status file
        with open(job_file_path, 'r') as file:
            job_data = json.load(file)
        
        # Create consistent response structure
        clean_response = {
            "job_id": job_data.get("job_id"),
            "job_status": job_data.get("job_status"),
            "process_id": job_data.get("process_id")
        }
        
        # Add response data or error based on status
        if job_data.get("job_status") == "completed" and job_data.get("response"):
            clean_response["response"] = job_data["response"]["response"]
            clean_response["message"] = job_data["response"].get("message", "success")
            clean_response["run_time"] = job_data["response"].get("run_time")
            clean_response["total_time"] = job_data["response"].get("total_time")
        elif job_data.get("job_status") == "failed":
            clean_response["error"] = job_data.get("error") or (job_data.get("response", {}).get("message") if job_data.get("response") else "Unknown error")
        else:
            clean_response["response"] = None
        
        # Return clean, consistent response structure
        return clean_response, "/v1/toolkit/job/status", 200
        
    except Exception as e:
        logger.error(f"Error retrieving status for job {get_job_id}: {str(e)}")
        return {"error": f"Failed to retrieve job status: {str(e)}"}, "/v1/toolkit/job/status", 500 