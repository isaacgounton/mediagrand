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



from flask import request, jsonify, current_app, has_request_context, has_app_context
from functools import wraps
import jsonschema
import os
import json
import time
import tempfile
import logging
from config.config import LOCAL_STORAGE_PATH

# No module-level variables needed for the simplified approach

def validate_payload(schema):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if we're in a Flask request context
            if has_request_context():
                # We're in an HTTP request context, perform normal validation
                if not request.json:
                    return jsonify({"message": "Missing JSON in request"}), 400
                try:
                    # Pre-process boolean strings to actual booleans and numeric strings to numbers for validation
                    def convert_bools(obj):
                        if isinstance(obj, dict):
                            return {k: convert_bools(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_bools(item) for item in obj]
                        elif isinstance(obj, str):
                            # Convert boolean strings
                            if obj.lower() in ['true', 'false']:
                                return obj.lower() == 'true'
                            # Convert numeric strings to float or int
                            try:
                                # Try float first (handles both int and float)
                                if '.' in obj or 'e' in obj.lower():
                                    return float(obj)
                                else:
                                    # Check if it can be parsed as int, but still return float for consistency
                                    int(obj)  # Test if it's a valid integer
                                    return float(obj)  # Return as float for JSON schema number validation
                            except ValueError:
                                # Not a valid number, return as string
                                pass
                        return obj

                    data = convert_bools(request.json)
                    jsonschema.validate(instance=data, schema=schema)
                    # Store converted data in a custom attribute that the route can access
                    setattr(request, '_validated_json', data)
                except jsonschema.ValidationError as validation_error:
                    return jsonify({"message": f"Invalid payload: {validation_error.message}"}), 400
            else:
                # We're in a worker context (no request context)
                # Validation was already performed when the task was queued
                # So we can proceed without validating again
                pass
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_job_status(job_id, data):
    """
    Log job status to a file in the LOCAL_STORAGE_PATH/jobs folder
    
    Args:
        job_id (str): The unique job ID
        data (dict): Data to write to the log file
    """
    try:
        # Use LOCAL_STORAGE_PATH for consistency with job status reading
        jobs_dir = os.path.join(LOCAL_STORAGE_PATH, 'jobs')
        
        # Create jobs directory if it doesn't exist
        if not os.path.exists(jobs_dir):
            os.makedirs(jobs_dir, exist_ok=True)
        
        # Create or update the job log file
        job_file = os.path.join(jobs_dir, f"{job_id}.json")
        
        # Write data directly to file
        with open(job_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        # Log the error but don't crash the application
        logging.error(f"Job {job_id}: Failed to write job status: {str(e)}")

def queue_task_wrapper(bypass_queue=False):
    def decorator(f):
        @wraps(f)  # Add functools.wraps to preserve the original function name
        def wrapper(*args, **kwargs):
            # Check if we're in a Flask application context and request context
            if has_request_context() and has_app_context():
                # We're in an HTTP request context, use the normal queue mechanism
                return current_app.queue_task(bypass_queue=bypass_queue)(f)(*args, **kwargs)
            else:
                # We're in a worker context, just call the function directly
                # The queueing has already been handled
                return f(*args, **kwargs)
        return wrapper
    return decorator
