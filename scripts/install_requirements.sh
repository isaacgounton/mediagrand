#!/bin/bash

# Enhanced requirements installation script for Coolify deployment
# This ensures all dependencies including YouTube authentication are properly installed

echo "Installing Python requirements..."

# Install base requirements
pip install -r requirements.txt

# Ensure yt-dlp OAuth2 plugin is installed (in case it's not in requirements.txt)
echo "Installing yt-dlp OAuth2 plugin..."
pip install yt-dlp-youtube-oauth2

# Create necessary directories for YouTube authentication
echo "Setting up YouTube authentication directories..."
mkdir -p /tmp/youtube_oauth
mkdir -p /tmp/youtube_cookies
mkdir -p /app/cookies

# Set proper permissions
chmod 755 /tmp/youtube_oauth
chmod 755 /tmp/youtube_cookies
chmod 755 /app/cookies

echo "Requirements installation completed!"

# Verify critical packages
echo "Verifying critical packages..."
python -c "import yt_dlp; print('✓ yt-dlp installed')"
python -c "import yt_dlp_youtube_oauth2; print('✓ yt-dlp-youtube-oauth2 installed')" || echo "⚠ yt-dlp-youtube-oauth2 not found - OAuth2 auth may not work"

echo "Setup complete!"

echo ""
echo "=== YOUTUBE AUTHENTICATION READY ==="
echo "Available authentication methods:"
echo "1. OAuth2 (automatic) - Most reliable for Docker/Coolify"
echo "2. cookies_content parameter - Pass cookies directly in API requests"
echo "3. cookies_url parameter - Download cookies from a URL"
echo "4. Cookie files - Place in /app/cookies/ directory"
echo ""
echo "For YouTube videos that require authentication, use:"
echo "- cookies_content: Pass raw cookie content in request body"
echo "- cookies_url: Provide URL to download cookies from"
echo ""
