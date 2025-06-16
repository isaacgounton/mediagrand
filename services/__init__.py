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

import os
import logging

logger = logging.getLogger(__name__)

# Ensure required directories exist
def ensure_required_directories():
    """Ensure all required directories exist"""
    from config import LOCAL_STORAGE_PATH
    
    directories = [
        LOCAL_STORAGE_PATH,
        os.path.join(LOCAL_STORAGE_PATH, 'models'),
        os.path.join(LOCAL_STORAGE_PATH, 'voices'),
        os.path.join(LOCAL_STORAGE_PATH, 'temp')
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")

# Create directories on module import
ensure_required_directories()
