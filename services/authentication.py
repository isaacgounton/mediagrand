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



from functools import wraps
from flask import request, jsonify, has_request_context
from config import API_KEY

def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if we're in a Flask request context
        if has_request_context():
            # We're in an HTTP request context, perform normal authentication
            api_key = request.headers.get('X-API-Key')
            
            if api_key != API_KEY:
                return jsonify({"message": "Unauthorized"}), 401
        else:
            # We're in a worker context (no request context)
            # Authentication was already performed when the task was queued
            # So we can proceed without checking again
            pass
            
        return func(*args, **kwargs)
    return wrapper
