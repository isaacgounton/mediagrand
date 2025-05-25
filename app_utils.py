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



from flask import request, jsonify, current_app
from functools import wraps
import jsonschema
import os
import json
import time
from config import LOCAL_STORAGE_PATH

def validate_payload(schema):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.json:
                return jsonify({"message": "Missing JSON in request"}), 400
            try:
                # Pre-process boolean strings to actual booleans for validation
                def convert_bools(obj):
                    if isinstance(obj, dict):
                        return {k: convert_bools(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_bools(item) for item in obj]
                    elif isinstance(obj, str) and obj.lower() in ['true', 'false']:
                        return obj.lower() == 'true'
                    return obj

                data = convert_bools(request.json)
                jsonschema.validate(instance=data, schema=schema)
                # Store converted data in a custom attribute that the route can access
                setattr(request, '_validated_json', data)
            except jsonschema.exceptions.ValidationError as validation_error:
                return jsonify({"message": f"Invalid payload: {validation_error.message}"}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_job_status(job_id, data):
    """
    Log job status to a file in the STORAGE_PATH/jobs folder
    
    Args:
        job_id (str): The unique job ID
        data (dict): Data to write to the log file
    """
    import tempfile
    import logging
    
    # Define primary and fallback directories
    primary_jobs_dir = os.path.join(LOCAL_STORAGE_PATH, 'jobs')
    fallback_jobs_dir = os.path.join(tempfile.gettempdir(), 'dahopevi_jobs')
    
    # Try primary directory first
    jobs_dir = primary_jobs_dir
    job_file = os.path.join(jobs_dir, f"{job_id}.json")
    
    # First attempt - try with primary directory
    try:
        # Create jobs directory if it doesn't exist
        if not os.path.exists(jobs_dir):
            try:
                os.makedirs(jobs_dir, mode=0o777, exist_ok=True)
            except (PermissionError, OSError):
                # If we can't set 777, try creating with default permissions
                os.makedirs(jobs_dir, exist_ok=True)
                
        # Try to make the directory writable if it exists
        try:
            if os.path.exists(jobs_dir):
                os.chmod(jobs_dir, 0o777)
        except (PermissionError, OSError):
            # Continue even if chmod fails
            pass
            
        # Write data directly to file
        with open(job_file, 'w') as f:
            json.dump(data, f, indent=2)
        return  # If successful, return early
            
    except (PermissionError, OSError) as e:
        logging.warning(f"Failed to write job status to primary location: {e}")
        
    # Fallback - try with temporary directory
    try:
        jobs_dir = fallback_jobs_dir
        job_file = os.path.join(jobs_dir, f"{job_id}.json")
        
        if not os.path.exists(jobs_dir):
            os.makedirs(jobs_dir, exist_ok=True)
            
        # Write data directly to file
        with open(job_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    except (PermissionError, OSError) as e:
        # Last resort - log the error but don't crash
        logging.error(f"Failed to write job status to fallback location: {e}")
        # In production, you might want to log this to a monitoring system

def queue_task_wrapper(bypass_queue=False):
    def decorator(f):
        @wraps(f)  # Add functools.wraps to preserve the original function name
        def wrapper(*args, **kwargs):
            return current_app.queue_task(bypass_queue=bypass_queue)(f)(*args, **kwargs)
        return wrapper
    return decorator
