# ====================================================================
# Stage 1: Python dependencies builder
# ====================================================================
FROM python:3.10-slim as python-builder

# Install only essential build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    git \
    pkg-config \
    libssl-dev \
    libffi-dev \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment for better dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
WORKDIR /app
COPY requirements.txt .

# Upgrade pip and install requirements with optimized flags
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium


# ====================================================================
# Stage 2: Final runtime image
# ====================================================================
FROM python:3.10-slim

# Install runtime dependencies including FFmpeg and Playwright browser dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Core system libraries
    libgomp1 \
    ca-certificates \
    curl \
    wget \
    # FFmpeg and multimedia libraries
    ffmpeg \
    # Font and media libraries
    fontconfig \
    fonts-liberation \
    imagemagick \
    # Essential audio/video libraries
    libmp3lame0 \
    libopus0 \
    libvorbis0a \
    libtheora0 \
    # Graphics libraries
    libfreetype6 \
    libfontconfig1 \
    libfribidi0 \
    libharfbuzz0b \
    # DRM and graphics acceleration libraries
    libdrm2 \
    libva2 \
    libva-drm2 \
    libvdpau1 \
    # System utilities
    xdg-utils \
    # Playwright browser dependencies (from working repo)
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgtk-3-0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get autoclean

# Copy Python virtual environment
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create appuser with minimal permissions (using -m flag like working repo)
RUN useradd -m appuser

# Copy application code
COPY . .

# Copy fonts and rebuild font cache
COPY ./fonts /usr/share/fonts/custom/
RUN fc-cache -f -v

# Create required directories and set permissions
RUN mkdir -p /tmp/assets /tmp/music /app/data/jobs /app/public/assets && \
    chown -R appuser:appuser /app /tmp/assets /tmp/music && \
    chmod -R 777 /app/data

# Install Playwright browsers as appuser to ensure proper permissions
USER appuser
RUN --mount=type=cache,target=/root/.cache/ms-playwright \
    playwright install chromium

# Create lightweight placeholder files using Python script
RUN python3 scripts/create_placeholders.py

# Create startup script for RQ workers and Gunicorn (simplified like working repo)
RUN echo '#!/bin/bash\n\
\n\
# Handle SIGTERM for graceful shutdown\n\
cleanup() {\n\
    echo "Received SIGTERM, shutting down..."\n\
    kill ${pids[@]}\n\
    wait\n\
    exit 0\n\
}\n\
\n\
trap cleanup SIGTERM\n\
\n\
# Array to store background process PIDs\n\
declare -a pids\n\
\n\
# Start RQ workers with correct settings\n\
for i in $(seq 1 ${RQ_WORKERS:-2}); do\n\
    python start_worker.py & # Use custom worker script to avoid CLI conflicts\n\
    pids+=($!)\n\
done\n\
\n\
# Start Gunicorn\n\
gunicorn --bind 0.0.0.0:8080 \\\n\
    --workers ${GUNICORN_WORKERS:-2} \\\n\
    --timeout ${GUNICORN_TIMEOUT:-300} \\\n\
    --worker-class sync \\\n\
    --keep-alive 80 \\\n\
    --preload \\\n\
    app:app &\n\
pids+=($!)\n\
\n\
# Wait for all processes\n\
wait' > /app/run_services.sh && \
    chmod +x /app/run_services.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEFAULT_BACKGROUND_VIDEO="/tmp/assets/placeholder.jpg" \
    DEFAULT_BACKGROUND_MUSIC="/tmp/music/default.wav" \
    PATH="/opt/venv/bin:$PATH"

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["/app/run_services.sh"]

# Pre-download the most accurate Whisper model (large-v3) at build time
# Pre-download the most accurate Whisper model (large-v3) at build time using persistent Docker layers
RUN --mount=type=cache,target=/root/.cache/whisper \
    python3 -c "import whisper; whisper.load_model('base')"
