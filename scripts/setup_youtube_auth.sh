#!/bin/bash

# Setup script for YouTube authentication on Coolify deployment
# This script should be run during the Docker build process

echo "Setting up YouTube authentication..."

# Create necessary directories
mkdir -p /tmp/youtube_oauth
mkdir -p /tmp/youtube_cookies
mkdir -p /app/cookies

# Set permissions
chmod 755 /tmp/youtube_oauth
chmod 755 /tmp/youtube_cookies
chmod 755 /app/cookies

# Install yt-dlp OAuth2 plugin
echo "Installing yt-dlp OAuth2 plugin..."
pip install yt-dlp-youtube-oauth2

echo "YouTube authentication setup completed!"

# Print environment variables that should be set
echo ""
echo "=== ENVIRONMENT VARIABLES TO SET IN COOLIFY ==="
echo "YOUTUBE_OAUTH_CACHE_DIR=/tmp/youtube_oauth"
echo "YOUTUBE_COOKIES_DIR=/tmp/youtube_cookies"
echo ""
echo "=== COOKIE AUTHENTICATION METHODS ==="
echo "1. OAuth2 (automatic) - Most reliable"
echo "2. cookies_content parameter - Pass cookies directly in API request"
echo "3. cookies_url parameter - Download cookies from a URL"
echo "4. Cookie files - Mount cookie files in /app/cookies/"
echo ""
echo "=== TESTING ==="
echo "Test with Simone endpoint:"
echo "curl -X POST https://your-domain.com/v1/simone/process_video \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'x-api-key: YOUR_API_KEY' \\"
echo "  -d '{\"video_url\": \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}'"
echo ""
echo "Or with cookies:"
echo "curl -X POST https://your-domain.com/v1/simone/process_video \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'x-api-key: YOUR_API_KEY' \\"
echo "  -d '{\"video_url\": \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\", \"cookies_url\": \"https://your-url.com/cookies.txt\"}'"
echo ""
