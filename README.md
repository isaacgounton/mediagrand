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

## Contributing

1. Choose royalty-free music files
2. Add them to `storage/music/` with appropriate mood prefixes
3. Test with different voice and music combinations

## License

This project is licensed under the GNU General Public License v2.0 (GPL-2.0).
