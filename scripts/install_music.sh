#!/bin/bash

# Create music directory if it doesn't exist
MUSIC_DIR="storage/music"
mkdir -p $MUSIC_DIR

# Function to download and tag a music file
download_music() {
    local url=$1
    local filename=$2
    local mood=$3
    
    echo "Downloading $mood music: $filename"
    curl -L "$url" -o "$MUSIC_DIR/${mood}_${filename}"
}

# Download sample music tracks from your preferred royalty-free music source
# Note: Replace these URLs with actual royalty-free music URLs from your collection

# Happy/Upbeat music
download_music "https://example.com/upbeat1.mp3" "happy_tune_1.mp3" "upbeat"
download_music "https://example.com/upbeat2.mp3" "happy_tune_2.mp3" "happy"

# Calm/Chill music
download_music "https://example.com/calm1.mp3" "peaceful_1.mp3" "calm"
download_music "https://example.com/chill1.mp3" "relaxed_1.mp3" "chill"

# Epic/Dramatic music
download_music "https://example.com/epic1.mp3" "epic_rise_1.mp3" "epic"
download_music "https://example.com/dramatic1.mp3" "intense_1.mp3" "dramatic"

# Dark/Mysterious music
download_music "https://example.com/dark1.mp3" "mysterious_1.mp3" "dark"

# Sad/Melancholic music
download_music "https://example.com/sad1.mp3" "melancholic_1.mp3" "sad"

echo "Music installation complete. Replace placeholder URLs with actual royalty-free music."
