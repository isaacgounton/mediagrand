# Build stage for compiling dependencies
FROM python:3.10-slim as builder

# Set build arguments for better resource control
ARG DOCKER_BUILDKIT=1
ARG BUILDKIT_INLINE_CACHE=1
ARG MAKEFLAGS="-j$(nproc)"

# Install Node.js and build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    ca-certificates \
    wget \
    tar \
    xz-utils \
    fonts-liberation \
    fontconfig \
    build-essential \
    yasm \
    cmake \
    meson \
    ninja-build \
    nasm \
    libssl-dev \
    libvpx-dev \
    libx264-dev \
    libx265-dev \
    libnuma-dev \
    libmp3lame-dev \
    libopus-dev \
    libvorbis-dev \
    libtheora-dev \
    libspeex-dev \
    libfreetype6-dev \
    libfontconfig1-dev \
    libgnutls28-dev \
    libaom-dev \
    libdav1d-dev \
    librav1e-dev \
    libsvtav1-dev \
    libzimg-dev \
    libwebp-dev \
    git \
    pkg-config \
    autoconf \
    automake \
    libtool \
    libfribidi-dev \
    libharfbuzz-dev \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Install SRT from source (latest version using cmake)
RUN git clone https://github.com/Haivision/srt.git && \
    cd srt && \
    mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf srt

# Install SVT-AV1 from source
RUN git clone https://gitlab.com/AOMediaCodec/SVT-AV1.git && \
    cd SVT-AV1 && \
    git checkout v0.9.0 && \
    cd Build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf SVT-AV1

# Install libvmaf from source
RUN git clone https://github.com/Netflix/vmaf.git && \
    cd vmaf/libvmaf && \
    meson build --buildtype release && \
    ninja -C build && \
    ninja -C build install && \
    cd ../.. && rm -rf vmaf && \
    ldconfig  # Update the dynamic linker cache

# Manually build and install fdk-aac (since it is not available via apt-get)
RUN git clone https://github.com/mstorsjo/fdk-aac && \
    cd fdk-aac && \
    autoreconf -fiv && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    cd .. && rm -rf fdk-aac

# Install libunibreak (required for ASS_FEATURE_WRAP_UNICODE)
RUN git clone https://github.com/adah1972/libunibreak.git && \
    cd libunibreak && \
    ./autogen.sh && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd .. && rm -rf libunibreak

# Build and install libass with libunibreak support and ASS_FEATURE_WRAP_UNICODE enabled
RUN git clone https://github.com/libass/libass.git && \
    cd libass && \
    autoreconf -i && \
    ./configure --enable-libunibreak || { cat config.log; exit 1; } && \
    mkdir -p /app && echo "Config log located at: /app/config.log" && cp config.log /app/config.log && \
    make -j$(nproc) || { echo "Libass build failed"; exit 1; } && \
    make install && \
    ldconfig && \
    cd .. && rm -rf libass

# Build and install FFmpeg with all required features
RUN git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg && \
    cd ffmpeg && \
    git checkout n7.0.2 && \
    PKG_CONFIG_PATH="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig" \
    CFLAGS="-I/usr/include/freetype2" \
    LDFLAGS="-L/usr/lib/x86_64-linux-gnu" \
    ./configure --prefix=/usr/local \
        --enable-gpl \
        --enable-pthreads \
        --enable-neon \
        --enable-libaom \
        --enable-libdav1d \
        --enable-librav1e \
        --enable-libsvtav1 \
        --enable-libvmaf \
        --enable-libzimg \
        --enable-libx264 \
        --enable-libx265 \
        --enable-libvpx \
        --enable-libwebp \
        --enable-libmp3lame \
        --enable-libopus \
        --enable-libvorbis \
        --enable-libtheora \
        --enable-libspeex \
        --enable-libass \
        --enable-libfreetype \
        --enable-libharfbuzz \
        --enable-fontconfig \
        --enable-libsrt \
        --enable-filter=drawtext \
        --extra-cflags="-I/usr/include/freetype2 -I/usr/include/libpng16 -I/usr/include" \
        --extra-ldflags="-L/usr/lib/x86_64-linux-gnu -lfreetype -lfontconfig" \
        --enable-gnutls \
    && make -j$(nproc) && \
    make install && \
    cd .. && rm -rf ffmpeg

# Add /usr/local/bin to PATH (if not already included)
ENV PATH="/usr/local/bin:${PATH}"

# Copy fonts into the custom fonts directory
COPY ./fonts /usr/share/fonts/custom

# Rebuild the font cache so that fontconfig can see the custom fonts
RUN fc-cache -f -v

# Set work directory
WORKDIR /app

# Set environment variable for Whisper cache
ENV WHISPER_CACHE_DIR="/app/whisper_cache"

# Create cache directory (no need for chown here yet)
RUN mkdir -p ${WHISPER_CACHE_DIR} 

# Copy the requirements file first to optimize caching
COPY requirements.txt .

# Upgrade pip and install requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt jsonschema

# Create the appuser 
RUN useradd -m appuser 

# Give appuser ownership of the /app directory (including whisper_cache)
RUN chown -R appuser:appuser /app

# Create NLTK data directory
RUN mkdir -p /usr/local/share/nltk_data && \
    chown -R appuser:appuser /usr/local/share/nltk_data

# Important: Switch to the appuser before downloading models
USER appuser

# Download required NLTK data
RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt averaged_perceptron_tagger stopwords

RUN python -c "import os; print(os.environ.get('WHISPER_CACHE_DIR')); import whisper; whisper.load_model('base')"

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Create directories for assets (no chown needed since we're already appuser)
RUN mkdir -p /tmp/assets && \
    mkdir -p /app/public/assets && \
    mkdir -p /app/remotion

# Setup Remotion environment (switch back to root temporarily)
USER root
WORKDIR /app/remotion
RUN npm install && \
    npm run build && \
    chown -R appuser:appuser /app/remotion && \
    # Fix webpack progress issue
    sed -i 's/new webpack.ProgressPlugin(),//' node_modules/@remotion/bundler/dist/webpack-config.js

# Switch back to appuser
USER appuser

# Back to app directory
WORKDIR /app

# Create placeholder video file
RUN ffmpeg -f lavfi -i color=c=black:s=1280x720:d=10 -c:v libx264 /tmp/assets/placeholder.mp4

# Create music directory and default music files
RUN mkdir -p /tmp/music && \
    ffmpeg -f lavfi -i "sine=frequency=440:duration=30" -c:a libmp3lame /tmp/music/default.mp3 && \
    ffmpeg -f lavfi -i "sine=frequency=523:duration=30" -c:a libmp3lame /tmp/music/upbeat_default.mp3 && \
    ffmpeg -f lavfi -i "sine=frequency=349:duration=30" -c:a libmp3lame /tmp/music/calm_default.mp3 && \
    ffmpeg -f lavfi -i "sine=frequency=294:duration=30" -c:a libmp3lame /tmp/music/sad_default.mp3

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEFAULT_BACKGROUND_VIDEO="/tmp/assets/placeholder.mp4" \
    DEFAULT_BACKGROUND_MUSIC="/tmp/music/default.mp3" \
    PEXELS_API_KEY=""

RUN echo '#!/bin/bash\n\
gunicorn --bind 0.0.0.0:8080 \
    --workers ${GUNICORN_WORKERS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-300} \
    --worker-class sync \
    --keep-alive 80 \
    app:app' > /app/run_gunicorn.sh && \
    chmod +x /app/run_gunicorn.sh

# Final stage
FROM python:3.10-slim

# Copy built artifacts from builder stage
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/include /usr/local/include
COPY --from=builder /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
COPY --from=builder /usr/share/fonts /usr/share/fonts
COPY --from=builder /usr/local/share/nltk_data /usr/local/share/nltk_data
COPY --from=builder /app /app
COPY --from=builder /tmp/assets /tmp/assets
COPY --from=builder /tmp/music /tmp/music

# Add non-free repositories for multimedia packages
RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# Install Node.js and runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    ca-certificates \
    curl \
    fontconfig \
    libssl3 \
    libvpx7 \
    libnuma1 \
    libmp3lame0 \
    libopus0 \
    libvorbis0a \
    libtheora0 \
    libspeex1 \
    libfreetype6 \
    libfontconfig1 \
    libgnutls30 \
    libzimg2 \
    libwebpmux3 \
    libfribidi0 \
    libharfbuzz0b \
    imagemagick && \
    # Try to install optional multimedia packages
    (apt-get install -y --no-install-recommends libx264-164 libx265-199 libaom3 libdav1d6 librav1e0 || true) && \
    rm -rf /var/lib/apt/lists/*

# Update library cache
RUN ldconfig

# Create required directories
RUN mkdir -p /tmp/assets && \
    mkdir -p /app/public/assets

# Set working directory
WORKDIR /app

# Create appuser
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

# Switch to appuser
USER appuser

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEFAULT_BACKGROUND_VIDEO="/tmp/assets/placeholder.mp4" \
    DEFAULT_BACKGROUND_MUSIC="/tmp/music/default.mp3" \
    PEXELS_API_KEY="" \
    PATH="/usr/local/bin:${PATH}" \
    NODE_ENV="production"

# Run the application
CMD ["/app/run_gunicorn.sh"]
