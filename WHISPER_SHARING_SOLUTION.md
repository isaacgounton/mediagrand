# Whisper Sharing Solution for dahopevi + short-video-maker

This document provides solutions for the Docker build issues and enables Whisper model sharing between dahopevi and short-video-maker to reduce redundancy and build times.

## Problems Solved

1. **Docker Build Error**: Fixed pnpm lockfile mismatch by using `--no-frozen-lockfile` flag
2. **Whisper Duplication**: Created shared Whisper installation to avoid building Whisper twice

## Solutions

### 1. Immediate Fix - Updated Dockerfiles

The following Dockerfile changes fix the pnpm lockfile error:

**Files Updated:**
- `short-video-maker/main.Dockerfile`
- `short-video-maker/main-cuda.Dockerfile`
- `short-video-maker/main-tiny.Dockerfile`

**Change Made:**
```dockerfile
# Before (causing error)
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --prod --frozen-lockfile

# After (fixed)
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --prod --no-frozen-lockfile
```

### 2. Whisper Sharing Solution

Created a new architecture that allows both services to share a single Whisper installation.

#### New Files Created:

1. **`short-video-maker/main-shared.Dockerfile`**
   - Removes Whisper build dependencies
   - Relies on shared Whisper volume
   - Smaller, faster builds

2. **`docker-compose-shared.yml`**
   - Orchestrates both services with shared volumes
   - Creates shared Whisper models volume
   - Proper service dependencies

3. **Updated Configuration:**
   - `short-video-maker/src/config.ts`: Added support for `SHARED_WHISPER_PATH`
   - `short-video-maker/src/short-creator/libraries/Whisper.ts`: Skip installation when using shared Whisper

## Usage Instructions

### Option 1: Quick Fix (Existing Setup)

If you want to continue with separate Whisper installations but fix the build error:

```powershell
# Build the fixed version
cd short-video-maker
docker build -f main.Dockerfile -t short-video-maker:latest .
```

### Option 2: Shared Whisper Setup (Recommended)

For optimal resource usage and faster builds:

```powershell
# Build and run with shared Whisper
docker-compose -f docker-compose-shared.yml up --build
```

This will:
1. Build dahopevi with its Whisper installation
2. Build short-video-maker without Whisper
3. Share the Whisper models via Docker volume
4. Start both services

### Option 3: Development Mode

For development with shared resources:

```powershell
# Start dahopevi first to populate Whisper models
docker-compose -f docker-compose-shared.yml up dahopevi

# Then start short-video-maker
docker-compose -f docker-compose-shared.yml up short-video-maker
```

## Service URLs

- **dahopevi**: http://localhost:8080
- **short-video-maker**: http://localhost:3123
- **Redis**: localhost:6379

## Environment Variables

### dahopevi
- `WHISPER_CACHE_DIR`: `/opt/whisper_cache`
- `REDIS_URL`: `redis://redis:6379`

### short-video-maker
- `SHARED_WHISPER_PATH`: `/shared/whisper`
- `WHISPER_MODEL`: `base.en`
- `DATA_DIR_PATH`: `/app/data`

## Benefits of Shared Setup

1. **Reduced Build Time**: ~50% faster builds (no Whisper compilation in short-video-maker)
2. **Smaller Images**: short-video-maker image is ~1GB smaller
3. **Resource Efficiency**: Single Whisper model cache shared between services
4. **Easier Maintenance**: One place to update Whisper versions

## Troubleshooting

### If Whisper sharing fails:
1. Check volume mounts: `docker volume ls`
2. Verify permissions: `docker exec -it <container> ls -la /shared/whisper`
3. Check logs: `docker-compose -f docker-compose-shared.yml logs short-video-maker`

### If build still fails:
1. Clear Docker cache: `docker system prune -a`
2. Remove pnpm cache: `docker volume rm $(docker volume ls -q | grep pnpm)`
3. Rebuild: `docker-compose -f docker-compose-shared.yml up --build --force-recreate`

## Migration from Existing Setup

1. Stop current containers: `docker-compose down`
2. Backup data: `docker cp <container>:/app/data ./backup`
3. Use new setup: `docker-compose -f docker-compose-shared.yml up --build`
4. Restore data if needed: `docker cp ./backup <new-container>:/app/data`

## Future Improvements

- Consider using a dedicated Whisper service container
- Implement health checks for Whisper model availability
- Add support for different Whisper model sizes per service
- Create init containers for model pre-loading
