# Deployment Guide

## File Structure for Deployment

This project maintains docker files in strategic locations to support different deployment scenarios:

```
mediagrand/
├── docker-compose.yml          # Root level - for Coolify auto-discovery
├── .dockerignore               # Root level - required for Docker builds
├── .env                        # Root level - environment variables
├── docker/
│   ├── docker-compose.yml      # Organized location - for development
│   ├── docker-compose.prod.yml # Production configuration
│   ├── Dockerfile              # Main Docker image
│   └── .dockerignore           # Backup copy
```

## Docker File Discovery During Deployment

### ✅ **Files that WILL be discovered:**
1. **`docker-compose.yml`** (root) - Coolify auto-discovery ✅
2. **`docker/Dockerfile`** - Referenced by docker-compose.yml ✅
3. **`.dockerignore`** (root) - Used during Docker build ✅
4. **`.env`** (root) - Environment variables ✅

### ⚠️ **Important Notes:**
- **`.dockerignore`** must be in root for Docker to use it during builds
- **`Dockerfile`** can be in subdirectory when referenced in docker-compose.yml
- **`docker-compose.yml`** must be in root for Coolify auto-discovery

## Deployment Options

### 1. Coolify Deployment (Automatic)
- **File used**: `/docker-compose.yml` (root level)
- **Auto-discovery**: Coolify automatically finds and uses this file
- **Configuration**: Points to `docker/Dockerfile` for builds

### 2. Manual Docker Compose (Development)
- **File used**: `/docker/docker-compose.yml`
- **Usage**: `cd docker && docker-compose up`
- **Benefits**: Keeps development files organized

### 3. Production Deployment
- **File used**: `/docker/docker-compose.prod.yml`
- **Usage**: `cd docker && docker-compose -f docker-compose.prod.yml up`
- **Features**: Production-optimized settings

## Coolify Configuration

### Deployment Settings in Coolify:
1. **Source Type**: Git Repository
2. **Build Pack**: Docker Compose
3. **Docker Compose File**: `docker-compose.yml` (auto-detected)
4. **Environment Variables**: Configure through Coolify UI or use `.env`

### Environment Variables for Coolify:
Ensure these are set in Coolify's environment configuration:
- `API_KEY`
- `APP_DOMAIN` 
- `S3_*` variables
- `OPENAI_API_KEY`
- Other required variables from `.env`

## File Synchronization

To keep files in sync after making changes:

```bash
# After editing docker/docker-compose.yml
cp docker/docker-compose.yml .
sed -i 's/context: \.\./context: ./g' docker-compose.yml

# After editing docker/.dockerignore  
cp docker/.dockerignore .

# After editing root files, sync back to docker folder
cp docker-compose.yml docker/
cp .dockerignore docker/
sed -i 's/context: \./context: ../g' docker/docker-compose.yml
```

## Troubleshooting

### Common Deployment Issues

1. **File not found errors** (e.g., `run_services.sh: not found`)
   - **Cause**: Dockerfile references moved to organized folders
   - **Solution**: Update Dockerfile paths to reflect new structure
   - **Example**: `COPY run_services.sh` → `COPY scripts/run_services.sh`

2. **Build context issues**
   - **Cause**: Wrong build context in docker-compose.yml
   - **Solution**: Ensure root docker-compose.yml uses `context: .`

3. **Missing .dockerignore**
   - **Cause**: .dockerignore in wrong location
   - **Solution**: Must be in root directory for Docker builds

### Validation

Run the deployment validation script:
```bash
./scripts/validate_deployment.sh
```

This checks all required files and configurations before deployment.

## Best Practices

1. **Edit the organized version**: Make changes in `docker/docker-compose.yml`
2. **Sync to root**: Copy to root for Coolify deployment
3. **Environment variables**: Use Coolify's environment management
4. **Secrets**: Use Coolify's secret management for sensitive data
5. **Monitoring**: Enable Coolify's monitoring and logging features
6. **Validate before deploy**: Always run validation script before deployment