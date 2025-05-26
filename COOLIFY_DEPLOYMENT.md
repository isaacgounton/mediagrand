# Coolify Deployment Guide

## Permission Issue Fix

The short-video-maker application was experiencing permission issues when trying to create directories in cloud environments like Coolify. The error was:

```
EACCES: permission denied, mkdir '/app/data/videos'
```

## Changes Made

### 1. Modified Dockerfile (`short-video-maker/main-shared.Dockerfile`)
- Commented out `USER appuser` to run as root in cloud environments
- Set directory permissions to 777 for `/app/data` to ensure write access
- Removed user ownership changes that can conflict with cloud orchestrators

### 2. Updated Application Code (`short-video-maker/src/config.ts`)
- Added try-catch block around directory creation
- Application now gracefully handles permission errors instead of crashing
- Logs warnings but continues execution when directories can't be created

### 3. Modified Docker Compose (`docker-compose-shared.yml`)
- Changed from bind mount `./short-video-maker/data:/app/data` to named volume `short_video_data:/app/data`
- Named volumes work better in cloud environments and avoid host filesystem permission conflicts
- Added `short_video_data` volume definition

## Deployment to Coolify

1. Use the `docker-compose-shared.yml` file for deployment
2. Set required environment variables:
   - `PEXELS_API_KEY` (required for video generation)
   - `DAHOPEVI_API_KEY` (optional, for integration with main API)
3. The application will now handle directory creation gracefully
4. Named volumes ensure proper permissions in cloud environments

## Environment Variables for Coolify

```env
PEXELS_API_KEY=your_pexels_api_key_here
DAHOPEVI_API_KEY=optional_api_key
NODE_ENV=production
DOCKER=true
WHISPER_MODEL=base.en
CONCURRENCY=2
VIDEO_CACHE_SIZE_IN_BYTES=2097152000
```

The application should now start successfully without permission errors.
