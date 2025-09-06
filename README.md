# 🎬 MediaGrand API

> **Professional Media Processing & Video Generation Platform**

A powerful, self-contained API for creating professional videos, processing media, and generating content at scale. Built with Python Flask and optimized for production deployment.

## ✨ What MediaGrand Does

MediaGrand transforms how you create and process media content:

### 🎥 **Automated Video Creation**
- **TTS Captioned Videos**: Convert text to professional videos with AI voice-over, captions, and cinematic effects
- **Viral Short Videos**: AI-powered compilation of viral moments from long-form content
- **Custom Video Processing**: Cut, trim, concatenate, and enhance videos with professional effects

### 🎙️ **Voice & Audio Processing**
- **Text-to-Speech**: Generate natural-sounding voice-overs in multiple languages using local edge-TTS
- **Audio Transcription**: Convert speech to text with high accuracy
- **Audio Enhancement**: Process, convert, and optimize audio files

### 🖼️ **Image & Visual Effects**
- **Image-to-Video**: Transform static images into dynamic videos with Ken Burns effect, zoom, and pan
- **Advanced Typography**: Professional caption styling with 70+ fonts, shadows, strokes, and positioning
- **Visual Effects**: Cinematic image effects for professional content creation

### 📊 **Media Intelligence**
- **Content Analysis**: Extract metadata, detect silence, analyze media properties
- **AI Content Generation**: Generate scripts, descriptions, and content using integrated AI models
- **Batch Processing**: Handle multiple files and operations efficiently

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/isaacgounton/mediagrand.git
cd mediagrand

# Copy environment template
cp .env.example .env

# Edit .env and set your API_KEY
nano .env

# Start with Docker Compose
docker-compose up -d

# Test the API
curl -H "X-API-Key: your-api-key" http://localhost:8080/v1/toolkit/test
```

### Option 2: Local Development

```bash
# Clone and setup
git clone https://github.com/isaacgounton/mediagrand.git
cd mediagrand

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Run the application
python app.py
```

## 📖 API Examples

### Create a Professional Video with Voice-Over

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "background_url": "https://example.com/background.jpg",
    "text": "Welcome to our amazing product demonstration",
    "width": 1080,
    "height": 1920,
    "image_effect": "ken_burns",
    "caption_font_name": "Arial",
    "caption_font_size": 120,
    "caption_font_bold": true,
    "caption_font_color": "#FFFFFF",
    "caption_position": "bottom"
  }' \
  http://localhost:8080/v1/video/tts-captioned
```

### Generate Viral Short Videos

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/long-video.mp4",
    "style": "viral_compilation",
    "duration": 60,
    "segments": 5
  }' \
  http://localhost:8080/v1/video/viral-shorts
```

### Convert Text to Speech

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a professional voice-over",
    "voice": "en-US-AriaNeural",
    "speed": 1.0
  }' \
  http://localhost:8080/v1/audio/speech
```

## 🎯 Core Features

### 🎬 Video Generation & Processing
| Feature | Description | Endpoint |
|---------|-------------|----------|
| **TTS Captioned Videos** | Create videos with AI voice-over, captions, and effects | `/v1/video/tts-captioned` |
| **Viral Short Videos** | AI-powered viral moment compilation | `/v1/video/viral-shorts` |
| **Long-form Videos** | Professional long-form content generation | `/v1/video/long-form` |
| **Video Editing** | Cut, trim, concatenate, split videos | `/v1/video/*` |
| **Caption Videos** | Add stylized captions to existing videos | `/v1/video/caption` |

### 🎙️ Audio & Voice
| Feature | Description | Endpoint |
|---------|-------------|----------|
| **Text-to-Speech** | Generate voice-overs with local edge-TTS | `/v1/audio/speech` |
| **Voice Discovery** | List available voices and languages | `/v1/audio/speech/voices` |
| **Audio Processing** | Convert, concatenate, enhance audio | `/v1/audio/*` |
| **Transcription** | Convert speech to text | `/v1/media/transcribe` |

### 🖼️ Image & Visual Effects
| Feature | Description | Endpoint |
|---------|-------------|----------|
| **Image to Video** | Transform images with cinematic effects | `/v1/image/to-video` |
| **Font Management** | 70+ professional fonts available | `/v1/video/fonts` |
| **Visual Effects** | Ken Burns, zoom, pan effects | *Integrated* |
| **Image Processing** | Convert, resize, optimize images | `/v1/image/*` |

### 🛠️ Media Tools
| Feature | Description | Endpoint |
|---------|-------------|----------|
| **Media Download** | Download from YouTube, social media | `/v1/media/download` |
| **Format Conversion** | Convert between media formats | `/v1/media/convert` |
| **Metadata Extraction** | Analyze media properties | `/v1/media/metadata` |
| **Silence Detection** | Find quiet segments in audio | `/v1/media/silence` |

### ☁️ Storage & Integration
| Feature | Description | Endpoint |
|---------|-------------|----------|
| **Cloud Storage** | Upload to S3, Google Cloud | `/v1/s3/upload` |
| **Webhook Support** | Real-time processing notifications | *All endpoints* |
| **Job Management** | Track processing status | `/v1/toolkit/jobs` |
| **Authentication** | Secure API access | `/v1/toolkit/authenticate` |

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
export API_KEY="your-api-key"
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
   APP_NAME=MediaGrand API
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

#### 2. Permission Denied Errors

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

#### 3. Missing Placeholder Assets

**Symptom**: Errors about missing placeholder.mp4 or default.wav

**Solutions**:
```bash
# Create placeholder assets
python scripts/create_placeholders.py

# Or rebuild Docker image
docker-compose build --no-cache
```

#### 4. FFmpeg Not Found

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

#### 5. Memory Issues

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

#### 6. Slow Build Times

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

## License

This project is licensed under the GNU General Public License v2.0 (GPL-2.0).
