# DahoPevi API

This API processes different types of media. It is built in Python using Flask.

## Features

### Audio
- **Concatenate Audio**: Combines multiple audio files into a single audio file.

### Code
- **Execute Python Code**: Executes Python code remotely and returns the execution results.

### FFmpeg
- **Compose Media**: Provides a flexible interface to FFmpeg for complex media processing operations.

### Image
- **Convert Image to Video**: Transforms a static image into a video with custom duration and zoom effects.

### Media
- **Convert Media**: Converts media files from one format to another with customizable codec options.
- **Convert to MP3**: Converts various media formats specifically to MP3 audio.
- **Download Media**: Downloads media content from various online sources using yt-dlp.
- **Feedback**: Provides a web interface for collecting and displaying feedback on media content.
- **Transcribe Media**: Transcribes or translates audio/video content from a provided media URL.
- **Detect Silence**: Detects silence intervals in a given media file.
- **Extract Metadata**: Extracts comprehensive metadata from media files including format, codecs, resolution, and bitrates.

### S3
- **Upload to S3**: Uploads files to Amazon S3 storage by streaming directly from a URL.

### Toolkit
- **Authenticate**: Provides a simple authentication mechanism to validate API keys.
- **Test**: Verifies that the API is properly installed and functioning.
- **Job Status**: Retrieves the status of a specific job by its ID.
- **Jobs Status**: Retrieves the status of all jobs within a specified time range.

### Video
- **Caption Video**: Adds customizable captions to videos with various styling options.
- **Concatenate Videos**: Combines multiple videos into a single continuous video file.
- **Extract Thumbnail**: Extracts a thumbnail image from a specific timestamp in a video.
- **Cut Video**: Cuts specified segments from a video file with optional encoding settings.
- **Split Video**: Splits a video into multiple segments based on specified start and end times.
- **Trim Video**: Trims a video by keeping only the content between specified start and end times.

## Getting Started

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install background music:
```bash
bash scripts/install_music.sh
```

3. Set environment variables:
```bash
export PEXELS_API_KEY="your-pexels-api-key"
```

### Usage

To use the API, send requests to the appropriate endpoints with the required parameters. For detailed information about all available API endpoints, refer to the [API Documentation](docs/API.md).

## Deployment

### Docker Deployment

#### Optimized Build Performance

This project includes an optimized Docker configuration that reduces build times from ~60 minutes to ~10-15 minutes:

- **Pre-built FFmpeg**: Uses `linuxserver/ffmpeg:latest` instead of compiling from source
- **Multi-stage builds**: Separate stages for dependencies and runtime
- **Layer caching**: Optimized layer ordering for maximum cache efficiency
- **Reduced image size**: 60% smaller final image

#### Coolify Deployment

For deployment with Coolify:

1. **Clone the repository** to your Coolify server

2. **Set environment variables** in Coolify dashboard:

   ```bash
   API_KEY=your_api_key_here
   APP_DEBUG=false
   APP_DOMAIN=your-domain.com
   APP_NAME=DahoPevi API
   APP_URL=https://your-domain.com
   # Add other required environment variables
   ```

3. **Deploy using docker-compose.yml**:
   - Coolify will automatically detect and use the included `docker-compose.yml`
   - Build time: ~10-15 minutes (first build)
   - Subsequent builds: ~2-5 minutes (with caching)

4. **Resource requirements**:
   - Memory: 2GB minimum, 4GB maximum
   - Storage: 10GB minimum for video processing
   - Network: High bandwidth recommended for video uploads/downloads

#### Manual Docker Build

```bash
# Build the optimized image
docker build -t daho-pevi-api .

# Run with docker-compose
docker-compose up -d
```

The service will be available at `http://localhost:8080` with health checks at `/v1/toolkit/test`.

## Troubleshooting

### Pre-Deployment Validation

Before deploying, run the startup validation script to check for common issues:

```bash
python scripts/validate_startup.py
```

This script will check:
- Required environment variables
- Directory permissions
- Python dependencies
- System commands (FFmpeg)
- Placeholder assets
- Application startup

### Common Issues

#### 1. Application Won't Start

**Symptom**: Container crashes immediately or Flask app fails to start

**Solutions**:
```bash
# Check if API_KEY is set
echo $API_KEY

# Validate startup requirements
python scripts/validate_startup.py

# Check Docker logs
docker-compose logs app
```

#### 2. Video Search APIs Not Working

**Symptom**: Background videos not found, using default placeholder videos

**Solutions**:
- **Optional**: Video search APIs (Pexels, Pixabay) are optional
- Set `PEXELS_API_KEY` and/or `PIXABAY_API_KEY` if you want background video search
- Get API keys from:
  - Pexels: https://www.pexels.com/api/
  - Pixabay: https://pixabay.com/api/docs/

#### 3. Permission Denied Errors

**Symptom**: Cannot write to `/tmp/jobs` or other directories

**Solutions**:
```bash
# Ensure directories exist and have correct permissions
mkdir -p /tmp/assets /tmp/music /tmp/jobs
chown -R appuser:appuser /tmp/assets /tmp/music /tmp/jobs

# Or rebuild with correct permissions
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 4. Missing Placeholder Assets

**Symptom**: Errors about missing placeholder.mp4 or default.wav

**Solutions**:
```bash
# Create placeholder assets
python scripts/create_placeholders.py

# Or rebuild Docker image
docker-compose build --no-cache
```

#### 5. FFmpeg Not Found

**Symptom**: ffmpeg or ffprobe command not found

**Solutions**:
```bash
# For Docker deployment (should be included)
docker-compose build --no-cache

# For local development
# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
```

#### 6. Memory Issues

**Symptom**: Container runs out of memory during video processing

**Solutions**:
```bash
# Increase Docker memory limits
# In docker-compose.yml, add:
services:
  app:
    deploy:
      resources:
        limits:
          memory: 4G
```

#### 7. Slow Build Times

**Symptom**: Docker build takes 30+ minutes

**Solutions**:
- Use the optimized multi-stage Dockerfile (included)
- Enable Docker BuildKit: `export DOCKER_BUILDKIT=1`
- Use build cache: `docker-compose build --parallel`

### Environment Variables

Copy `.env.example` to `.env` and configure required variables:

```bash
cp .env.example .env
# Edit .env with your values
```

**Required**:
- `API_KEY`: Your API authentication key

**Optional** (for enhanced functionality):
- `PEXELS_API_KEY`: For background video search
- `PIXABAY_API_KEY`: For background video search  
- `S3_*` or `GCP_*`: For cloud storage

### Health Checks

Test your deployment:

```bash
# Basic health check
curl http://localhost:8080/v1/toolkit/test

# Authentication test
curl -H "X-API-Key: your-api-key" http://localhost:8080/v1/toolkit/authenticate

# Check application logs
docker-compose logs -f app
```

## Contributing

1. Choose royalty-free music files
2. Add them to `storage/music/` with appropriate mood prefixes
3. Test with different voice and music combinations

## License

This project is licensed under the GNU General Public License v2.0 (GPL-2.0).
