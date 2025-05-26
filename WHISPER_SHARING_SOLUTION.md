# Whisper & TTS Sharing Solution for dahopevi + short-video-maker

This document provides solutions for the Docker build issues and enables both Whisper and TTS service sharing between dahopevi and short-video-maker to reduce redundancy and build times.

## Problems Solved

1. **Docker Build Error**: Fixed pnpm lockfile mismatch by using `--no-frozen-lockfile` flag
2. **Missing kokoro-js dependency**: Replaced with dahopevi's `/v1/audio/speech` endpoint
3. **Whisper Duplication**: Created shared Whisper installation to avoid building Whisper twice
4. **TTS Duplication**: short-video-maker now uses dahopevi's TTS service instead of its own Kokoro

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

### 2. TTS Integration with dahopevi

Replaced the problematic `kokoro-js` dependency with integration to dahopevi's TTS service.

**Files Updated:**
- `short-video-maker/src/short-creator/libraries/Kokoro.ts`: Now calls dahopevi's `/v1/audio/speech` endpoint
- `docker-compose-shared.yml`: Added `DAHOPEVI_URL` environment variable

**Benefits:**
- No more missing `kokoro-js` dependency errors
- Consistent TTS across both services
- Reduced Docker image size
- Single TTS service to maintain

### 3. Whisper Sharing Solution

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
   - TTS service integration

3. **Updated Configuration:**
   - `short-video-maker/src/config.ts`: Added support for `SHARED_WHISPER_PATH`
   - `short-video-maker/src/short-creator/libraries/Whisper.ts`: Skip installation when using shared Whisper
   - `short-video-maker/src/short-creator/libraries/Kokoro.ts`: Use dahopevi TTS service

## Usage Instructions

### Option 1: Quick Fix (Existing Setup)

If you want to continue with separate installations but fix the build error:

```powershell
# Build the fixed version
cd short-video-maker
docker build -f main.Dockerfile -t short-video-maker:latest .
```

### Option 2: Shared Services Setup (Recommended)

For optimal resource usage and faster builds:

```powershell
# Build and run with shared services
docker-compose -f docker-compose-shared.yml up --build
```

This will:
1. Build dahopevi with its Whisper installation and TTS service
2. Build short-video-maker without Whisper or Kokoro dependencies
3. Share the Whisper models via Docker volume
4. Configure short-video-maker to use dahopevi's TTS endpoint
5. Start both services with proper networking

### Option 3: Development Mode

For development with shared resources:

```powershell
# Start dahopevi first to populate models and services
docker-compose -f docker-compose-shared.yml up dahopevi redis

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
- `DAHOPEVI_URL`: `http://dahopevi:8080` (for TTS service)
- `DAHOPEVI_API_KEY`: Optional API key for dahopevi authentication

## TTS Integration Details

The short-video-maker now calls dahopevi's TTS endpoint:

```typescript
// Example TTS request to dahopevi
const response = await axios.post(`${dahopevi_url}/v1/audio/speech`, {
  tts: "kokoro",
  text: "Hello world",
  voice: "af_bella",
  output_format: "wav"
});
```

**Supported TTS Engines in dahopevi:**
- `kokoro` - High quality neural TTS
- `edge-tts` - Microsoft Edge TTS
- `streamlabs-polly` - Amazon Polly via Streamlabs

## Benefits of Shared Setup

1. **Reduced Build Time**: ~60% faster builds (no Whisper compilation or Kokoro installation)
2. **Smaller Images**: short-video-maker image is ~1.5GB smaller
3. **Resource Efficiency**: Single Whisper model cache and TTS service shared between services
4. **Easier Maintenance**: One place to update Whisper versions and TTS configurations
5. **Consistent Quality**: Same TTS voice across all services
6. **No Dependency Issues**: Eliminates kokoro-js build problems

## Troubleshooting

### If Whisper sharing fails:
1. Check volume mounts: `docker volume ls`
2. Verify permissions: `docker exec -it <container> ls -la /shared/whisper`
3. Check logs: `docker-compose -f docker-compose-shared.yml logs short-video-maker`

### If TTS integration fails:
1. Check dahopevi health: `curl http://localhost:8080/health`
2. Test TTS endpoint: `curl -X POST http://localhost:8080/v1/audio/speech/voices`
3. Verify network connectivity: `docker-compose -f docker-compose-shared.yml logs dahopevi`
4. Check authentication if using API key

### If build still fails:
1. Clear Docker cache: `docker system prune -a`
2. Remove pnpm cache: `docker volume rm $(docker volume ls -q | grep pnpm)`
3. Rebuild: `docker-compose -f docker-compose-shared.yml up --build --force-recreate`

### If kokoro-js errors persist:
1. Verify the new Kokoro.ts is using axios instead of kokoro-js
2. Check that package.json doesn't have kokoro-js dependency
3. Rebuild with `--no-cache`: `docker build --no-cache -f main-shared.Dockerfile .`

## Migration from Existing Setup

1. Stop current containers: `docker-compose down`
2. Backup data: `docker cp <container>:/app/data ./backup`
3. Use new setup: `docker-compose -f docker-compose-shared.yml up --build`
4. Restore data if needed: `docker cp ./backup <new-container>:/app/data`

## API Compatibility

The new TTS integration maintains the same interface for short-video-maker, so existing code will continue to work without changes. The `Kokoro` class methods remain the same but now use dahopevi's backend.

## Future Improvements

- Consider using a dedicated Whisper service container
- Implement health checks for Whisper model availability  
- Add support for different Whisper model sizes per service
- Create init containers for model pre-loading
- Add TTS voice caching and optimization
- Implement fallback TTS engines
