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

"""
Request validation utilities for API endpoints.
"""

from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)


def validate_json_request(request_obj):
    """
    Validate that the request contains valid JSON data.
    
    Args:
        request_obj: Flask request object
        
    Returns:
        dict: The JSON data from the request
        
    Raises:
        ValueError: If request doesn't contain valid JSON
    """
    if not request_obj.is_json:
        raise ValueError("Request must contain JSON data")
    
    if not request_obj.json:
        raise ValueError("Request body is empty or invalid JSON")
    
    return request_obj.json
