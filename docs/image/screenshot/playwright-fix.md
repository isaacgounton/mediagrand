# Playwright Browser Installation Fix

## Problem
The `/v1/image/screenshot/webpage` endpoint was failing with the error:
```
BrowserType.launch: Executable doesn't exist at /app/.cache/ms-playwright/chromium_headless_shell-1169/chrome-linux/headless_shell
```

This error occurred because Playwright browsers were only installed in the Docker build stage but not properly copied to the final runtime image.

## Root Cause
The issue was in the multi-stage Docker build:
1. **Stage 1 (python-builder)**: Playwright Python package and browsers were installed
2. **Stage 2 (runtime)**: Only the Python virtual environment was copied, but Playwright browser binaries were lost

## Solution Applied

### 1. Fixed Dockerfile Multi-Stage Build
Updated [`Dockerfile`](../../../Dockerfile) to properly handle Playwright browsers:

**Before:**
```dockerfile
# Stage 1: Install playwright with browsers
RUN playwright install --with-deps chromium

# Stage 2: Only copy Python venv (browsers lost!)
COPY --from=python-builder /opt/venv /opt/venv
```

**After:**
```dockerfile
# Stage 1: Install only playwright package (no browsers to save build time)
RUN playwright install chromium

# Stage 2: Install browsers in final runtime stage
COPY --from=python-builder /opt/venv /opt/venv
RUN playwright install --with-deps chromium
```

### 2. Added Playwright Check Script
Created [`scripts/check_playwright.py`](../../../scripts/check_playwright.py) that:
- Tests if Playwright browsers are available
- Automatically installs them if missing
- Provides detailed logging for troubleshooting

### 3. Enhanced Startup Script
Modified the Docker startup script to:
- Run Playwright browser check on container startup
- Continue startup even if check fails (graceful degradation)
- Log status for monitoring

### 4. Improved Error Handling
Enhanced [`services/v1/image/screenshot_webpage.py`](../../../services/v1/image/screenshot_webpage.py) to:
- Detect Playwright browser missing errors
- Provide user-friendly error messages
- Guide users to retry after browser installation

## Files Modified
- [`Dockerfile`](../../../Dockerfile) - Fixed multi-stage build and added startup check
- [`scripts/check_playwright.py`](../../../scripts/check_playwright.py) - New browser verification script
- [`services/v1/image/screenshot_webpage.py`](../../../services/v1/image/screenshot_webpage.py) - Enhanced error handling

## Deployment Instructions

### For Coolify Deployment
1. **Commit Changes**: Ensure all modified files are committed to your repository
2. **Rebuild Container**: In Coolify, trigger a new build/deployment
3. **Monitor Logs**: Check startup logs to verify Playwright installation
4. **Test Endpoint**: Try the `/v1/image/screenshot/webpage` endpoint

### Build Command (if building manually)
```bash
docker build -t dahopevi-api .
```

### Verification
Test the endpoint with:
```bash
curl -X POST https://api.dahopevi.com/v1/image/screenshot/webpage \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "format": "png"}'
```

## Additional Notes
- The fix ensures browsers are installed in the runtime environment
- Build time may increase slightly due to browser download in runtime stage
- The check script provides a safety net for any future browser issues
- Error messages now guide users when browsers are missing

## Troubleshooting
If the issue persists:
1. Check container logs for Playwright installation messages
2. Verify the startup script is running the browser check
3. Ensure sufficient disk space for browser downloads (~200MB for Chromium)
4. Consider increasing container memory if installation fails