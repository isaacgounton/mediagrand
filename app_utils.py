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
import tempfile
import logging
from config import LOCAL_STORAGE_PATH

# No module-level variables needed for the simplified approach

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
    Log job status to a file in the original /tmp/jobs directory with proper permissions
    
    Args:
        job_id (str): The unique job ID
        data (dict): Data to write to the log file
    """
    # Keep using the original jobs directory that all endpoints expect
    jobs_dir = os.path.join('/tmp', 'jobs')
    
    # As a single fallback, use system temp dir if /tmp isn't available
    if not os.path.exists('/tmp') or not os.access('/tmp', os.W_OK):
        jobs_dir = os.path.join(tempfile.gettempdir(), 'jobs')
        logging.info(f"Using system temp directory for job status: {jobs_dir}")
    
    try:
        # Create the jobs directory if it doesn't exist
        # This should happen once at application startup
        if not os.path.exists(jobs_dir):
            os.makedirs(jobs_dir, mode=0o777, exist_ok=True)
            logging.info(f"Created jobs directory: {jobs_dir}")
        
        # Define the job file path
        job_file = os.path.join(jobs_dir, f"{job_id}.json")
        
        # Write the data to the file
        with open(job_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        logging.debug(f"Job {job_id}: Successfully wrote status to {job_file}")
    except Exception as e:
        # Log the error but don't crash the application
        logging.error(f"Job {job_id}: Failed to write job status: {str(e)}")

def queue_task_wrapper(bypass_queue=False):
    def decorator(f):
        @wraps(f)  # Add functools.wraps to preserve the original function name
        def wrapper(*args, **kwargs):
            return current_app.queue_task(bypass_queue=bypass_queue)(f)(*args, **kwargs)
        return wrapper
    return decorator
