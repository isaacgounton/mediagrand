# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MediaGrand is a comprehensive Flask-based API for video and audio processing with AI capabilities. The application provides media transcription, format conversion, video editing, text-to-speech, and AI-powered content generation services.

## Development Commands

### Development Environment
```bash
# Start development environment with live reload
./dev.sh

# Start local development without Docker
./local.sh

# Run services with Docker Compose
./run_services.sh
```

### Production Deployment
```bash
# Build and push Docker image
./push-docker.sh

# Deploy with production profile
docker-compose --profile production up -d
```

### Testing and Validation
```bash
# Run startup validation
python scripts/validate_startup.py

# Check Python environment
python scripts/check_environment.py

# Test Playwright installation
python scripts/check_playwright.py

# Create placeholder assets
python scripts/create_placeholders.py
```

### Health Checks
```bash
# Test API health
curl http://localhost:8080/health

# Test authentication
curl -H "X-API-Key: your-api-key" http://localhost:8080/v1/toolkit/authenticate

# Basic API test
curl http://localhost:8080/v1/toolkit/test
```

## Architecture Overview

### Core Application Structure
- **app.py**: Main Flask application with Redis Queue (RQ) integration
- **config.py**: Environment configuration and validation
- **routes/**: HTTP endpoints organized by API version
- **services/**: Business logic services (authentication, media processing, AI)
- **workers/**: Background job processing
- **templates/**: HTML templates for admin interface

### Service Architecture
The application follows a layered service pattern with these main categories:

#### Authentication & Security
- Basic API key authentication (`services/authentication.py`)
- Enhanced authentication with rate limiting (`services/enhanced_authentication.py`)
- Request validation utilities (`services/request_validation.py`)

#### AI/ML Services
- Google Gemini integration (`services/v1/ai/gemini_service.py`)
- Long-form content generation (`services/v1/ai/long_form_ai_service.py`)
- Music generation with MusicGen (`services/v1/audio/musicgen.py`)

#### Media Processing
- Advanced Whisper transcription (`services/transcription.py`)
- FFmpeg media processing (`services/ffmpeg_toolkit.py`)
- Text-to-speech with Edge TTS (`services/v1/audio/tts/`)

#### Cloud Storage
- Abstract storage provider interface (`services/cloud_storage.py`)
- S3-compatible storage (`services/s3_toolkit.py`)
- Google Cloud Platform storage (`services/gcp_toolkit.py`)

#### Specialized Services
- Simone AI processor for video-to-blog conversion (`services/simone/processor.py`)
  - Unified endpoint with optional features: transcription, blog, topics, X threads
  - Improved blog generation prompt for direct content without explanations
- YouTube authentication (`services/youtube_auth.py`)
- Webhook notifications (`services/webhook.py`)

### Queue System
- Redis Queue (RQ) for background processing
- Job status tracking and progress updates
- Context-aware authentication for workers
- Configurable queue length limits

### API Structure
- **v1 API**: Primary API endpoints under `/v1/`
- **Legacy API**: Backward compatibility endpoints
- **Admin API**: Management interface under `/admin/`

## Environment Configuration

### Required Environment Variables
```bash
API_KEY=your_api_key_here
REDIS_URL=redis://redis:6379/0
```

### Optional Configuration
```bash
# Storage providers
GCP_BUCKET_NAME=your-bucket
GCP_SA_CREDENTIALS=path/to/credentials.json
S3_ACCESS_KEY=your-s3-key
S3_SECRET_KEY=your-s3-secret
S3_BUCKET_NAME=your-s3-bucket

# AI services
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=google/gemma-3-12b-it:free
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Video search APIs
PIXABAY_API_KEY=your-pixabay-key

```

## Development Workflow

### Adding New Endpoints
1. Create route in `routes/v1/[category]/[endpoint].py`
2. Implement service logic in `services/v1/[category]/[service].py`
3. Add authentication decorator if needed
4. Register blueprint in `app.py`
5. Update homepage route with new endpoint

### Authentication
Use the `@requires_auth` decorator for protected endpoints:
```python
from services.enhanced_authentication import requires_auth

@bp.route('/protected-endpoint', methods=['POST'])
@requires_auth()
def protected_function():
    pass
```

### Background Jobs
Use the `@queue_task()` decorator for long-running operations:
```python
from app import queue_task

@queue_task()
def process_video(job_id, data):
    # Long-running task
    pass
```

### Error Handling
- Use standardized error responses
- Log errors with context
- Clean up temporary files in finally blocks
- Return appropriate HTTP status codes

## Key Dependencies

### Core Framework
- Flask 3.0.2 with CORS support
- Redis Queue (RQ) for background processing
- Gunicorn for production deployment

### Media Processing
- FFmpeg for video/audio processing
- OpenAI Whisper for transcription
- Pillow for image processing
- MoviePy for video editing

### AI/ML
- Google Gemini API
- OpenAI-compatible models
- Meta's MusicGen (torch-based)
- Edge TTS for speech synthesis

### Storage & Cloud
- Google Cloud Storage
- AWS S3 (boto3)
- DigitalOcean Spaces

## Testing

### Local Testing
```bash
# Start development environment
./dev.sh

# Test specific endpoint
curl -X POST http://localhost:8080/v1/toolkit/test
```

### Docker Testing
```bash
# Build and test with Docker
docker-compose build api-dev
docker-compose up api-dev redis
```

## Deployment Notes

### Docker Deployment
- Uses multi-stage builds for optimization
- Includes FFmpeg pre-built to reduce build time
- Supports both development and production profiles
- Automatic health checks and restarts

### Resource Requirements
- Memory: 2GB minimum, 4GB recommended
- Storage: 10GB minimum for video processing
- Network: High bandwidth for video uploads/downloads

### Production Considerations
- Set `APP_DEBUG=false` in production
- Configure proper logging levels
- Set up monitoring for Redis and worker processes
- Use persistent volumes for data and models