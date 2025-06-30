# Copyright (c) 2025 Isaac Gounton

import os
import json
import logging
from flask import Blueprint, request
from config import LOCAL_STORAGE_PATH
from services.enhanced_authentication import enhanced_authenticate, require_permission

v1_toolkit_job_status_bp = Blueprint('v1_toolkit_job_status', __name__)
logger = logging.getLogger(__name__)

@v1_toolkit_job_status_bp.route('/v1/jobs/<job_id>/status', methods=['GET'])
@enhanced_authenticate
@require_permission('read')
def get_job_status(job_id):
    """
    Get the status of a specific job
    
    Args:
        job_id (str): The job ID to get status for
    
    Returns:
        JSON response with job status information
    """
    logger.info(f"Retrieving status for job {job_id}")
    
    try:
        # Construct the path to the job status file
        job_file_path = os.path.join(LOCAL_STORAGE_PATH, 'jobs', f"{job_id}.json")
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
            
            return {
                "success": False,
                "error": "Job not found",
                "message": f"Job {job_id} not found",
                "jobId": job_id
            }, f"/v1/jobs/{job_id}/status", 404
        
        # Read the job status file
        with open(job_file_path, 'r') as file:
            job_data = json.load(file)
        
        # Determine job status and create response
        job_status = job_data.get("job_status", "unknown")
        
        response = {
            "success": True,
            "jobId": job_id,
            "status": job_status,
            "statusUrl": f"/v1/jobs/{job_id}/status"
        }
        
        # Add different fields based on job status
        if job_status == "completed":
            if job_data.get("response"):
                response["message"] = "Job completed successfully"
                response["result"] = job_data["response"].get("response")
                response["executionTime"] = {
                    "run_time": job_data["response"].get("run_time"),
                    "total_time": job_data["response"].get("total_time"),
                    "queue_time": job_data["response"].get("queue_time")
                }
                # Add download URL if the result contains a file URL
                if isinstance(response["result"], dict) and "url" in response["result"]:
                    response["downloadUrl"] = response["result"]["url"]
            else:
                response["message"] = "Job completed but no result data available"
                
        elif job_status == "failed":
            response["success"] = False
            response["message"] = "Job failed"
            response["error"] = job_data.get("error") or (
                job_data.get("response", {}).get("message") 
                if job_data.get("response") else "Unknown error"
            )
            
        elif job_status == "processing":
            response["message"] = "Job is currently processing"
            
        else:
            response["message"] = f"Job status: {job_status}"
        
        # Add metadata
        response["processId"] = job_data.get("process_id")
        response["createdAt"] = job_data.get("created_at")
        response["updatedAt"] = job_data.get("updated_at")
        
        return response, f"/v1/jobs/{job_id}/status", 200
        
    except Exception as e:
        logger.error(f"Error retrieving status for job {job_id}: {str(e)}")
        return {
            "success": False,
            "error": "Internal server error",
            "message": f"Failed to retrieve job status: {str(e)}",
            "jobId": job_id
        }, f"/v1/jobs/{job_id}/status", 500

@v1_toolkit_job_status_bp.route('/v1/jobs', methods=['POST'])
@enhanced_authenticate
@require_permission('write')
def create_job():
    """
    Create a new job and return job information
    This is a utility endpoint for testing job creation
    """
    import uuid
    
    job_id = str(uuid.uuid4())
    
    response = {
        "success": True,
        "message": "Job created successfully", 
        "jobId": job_id,
        "statusUrl": f"/v1/jobs/{job_id}/status"
    }
    
    return response, "/v1/jobs", 201

# Legacy endpoint for backward compatibility
@v1_toolkit_job_status_bp.route('/v1/toolkit/job_status', methods=['POST'])
@enhanced_authenticate
@require_permission('read')
def legacy_job_status():
    """Legacy job status endpoint for backward compatibility"""
    data = request.get_json()
    if not data or "job_id" not in data:
        return {
            "success": False,
            "error": "Missing job_id in request body"
        }, "/v1/toolkit/job_status", 400
    
    job_id = data["job_id"]
    
    # Redirect to new endpoint logic
    try:
        job_file_path = os.path.join(LOCAL_STORAGE_PATH, 'jobs', f"{job_id}.json")
        
        if not os.path.exists(job_file_path):
            return {"error": "Job not found", "job_id": job_id}, "/v1/toolkit/job_status", 404
        
        with open(job_file_path, 'r') as file:
            job_data = json.load(file)
        
        # Return in legacy format
        clean_response = {
            "job_id": job_data.get("job_id"),
            "job_status": job_data.get("job_status"),
            "process_id": job_data.get("process_id")
        }
        
        if job_data.get("job_status") == "completed" and job_data.get("response"):
            clean_response["response"] = job_data["response"]["response"]
            clean_response["message"] = job_data["response"].get("message", "success")
            clean_response["run_time"] = job_data["response"].get("run_time")
            clean_response["total_time"] = job_data["response"].get("total_time")
        elif job_data.get("job_status") == "failed":
            clean_response["error"] = job_data.get("error") or (
                job_data.get("response", {}).get("message") 
                if job_data.get("response") else "Unknown error"
            )
        else:
            clean_response["response"] = None
        
        return clean_response, "/v1/toolkit/job_status", 200
        
    except Exception as e:
        logger.error(f"Error in legacy job status for {job_id}: {str(e)}")
        return {"error": f"Failed to retrieve job status: {str(e)}"}, "/v1/toolkit/job_status", 500