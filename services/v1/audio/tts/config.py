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

# TTS Configuration
TTS_CONFIG = {
    # Default TTS settings
    "DEFAULT_VOICE": os.getenv('TTS_DEFAULT_VOICE', 'en-US-AvaNeural'),
    "DEFAULT_RESPONSE_FORMAT": os.getenv('TTS_DEFAULT_FORMAT', 'mp3'),
    "DEFAULT_SPEED": float(os.getenv('TTS_DEFAULT_SPEED', '1.0')),
    "DEFAULT_LANGUAGE": os.getenv('TTS_DEFAULT_LANGUAGE', 'en-US'),
    
    # Feature flags
    "REMOVE_FILTER": os.getenv('TTS_REMOVE_FILTER', 'false').lower() in ('true', '1', 'yes'),
    "DETAILED_ERROR_LOGGING": os.getenv('TTS_DETAILED_LOGGING', 'true').lower() in ('true', '1', 'yes'),
}

# Audio format to MIME type mapping
AUDIO_FORMAT_MIME_TYPES = {
    "mp3": "audio/mpeg",
    "opus": "audio/ogg",
    "aac": "audio/aac",
    "flac": "audio/flac",
    "wav": "audio/wav",
    "pcm": "audio/L16"
}
