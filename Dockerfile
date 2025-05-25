# ====================================================================
# Stage 1: Base image with pre-built FFmpeg
# ====================================================================
FROM linuxserver/ffmpeg:latest as ffmpeg-base

# ====================================================================
# Stage 2: Python dependencies builder
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
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment for better dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
WORKDIR /app
COPY requirements.txt .

# Upgrade pip and install requirements with optimized flags
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --find-links https://download.pytorch.org/whl/cpu \
    torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt jsonschema

# Download ML models in builder stage to avoid repeated downloads
ENV WHISPER_CACHE_DIR="/opt/whisper_cache"
RUN mkdir -p ${WHISPER_CACHE_DIR}
RUN python -c "import whisper; whisper.load_model('base')"

# Download NLTK data
RUN python -m nltk.downloader punkt averaged_perceptron_tagger stopwords

# ====================================================================
# Stage 3: Final runtime image
# ====================================================================
FROM python:3.10-slim

# Install only runtime dependencies (no build tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Core system libraries
    libgomp1 \
    ca-certificates \
    curl \
    wget \
    # Font and media libraries
    fontconfig \
    fonts-liberation \
    imagemagick \
    # Essential audio/video libraries (simplified to avoid version conflicts)
    libmp3lame0 \
    libopus0 \
    libvorbis0a \
    libtheora0 \
    # Graphics libraries
    libfreetype6 \
    libfontconfig1 \
    libfribidi0 \
    libharfbuzz0b \
    # System utilities
    xdg-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get autoclean

# Copy FFmpeg binaries from pre-built image
COPY --from=ffmpeg-base /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg-base /usr/local/bin/ffprobe /usr/local/bin/ffprobe

# Copy Python virtual environment
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy pre-downloaded models and NLTK data
COPY --from=python-builder /opt/whisper_cache /opt/whisper_cache
COPY --from=python-builder /root/nltk_data /usr/local/share/nltk_data

# Set working directory
WORKDIR /app

# Create appuser with minimal permissions
RUN useradd -r -s /bin/false -d /app appuser

# Copy application code
COPY . .

# Copy fonts and rebuild font cache
COPY ./fonts /usr/share/fonts/custom/
RUN fc-cache -f -v

# Create required directories and set permissions
RUN mkdir -p /tmp/assets /tmp/music /app/data/jobs /app/public/assets ${WHISPER_CACHE_DIR} && \
    chown -R appuser:appuser /app /tmp/assets /tmp/music ${WHISPER_CACHE_DIR} && \
    chmod -R 777 /app/data

# Generate placeholder assets as appuser (faster than FFmpeg)
USER appuser

# Create lightweight placeholder files using Python script
RUN python3 scripts/create_placeholders.py

# Create startup script
RUN echo '#!/bin/bash\n\
\n\
gunicorn --bind 0.0.0.0:8080 \
    --workers ${GUNICORN_WORKERS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-300} \
    --worker-class sync \
    --keep-alive 80 \
    --preload \
    app:app' > /app/run_gunicorn.sh && \
    chmod +x /app/run_gunicorn.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEFAULT_BACKGROUND_VIDEO="/tmp/assets/placeholder.jpg" \
    DEFAULT_BACKGROUND_MUSIC="/tmp/music/default.wav" \
    WHISPER_CACHE_DIR="/opt/whisper_cache" \
    PATH="/opt/venv/bin:$PATH"

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["/app/run_gunicorn.sh"]
