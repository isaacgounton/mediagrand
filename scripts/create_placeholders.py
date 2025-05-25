#!/usr/bin/env python3
"""
Script to create placeholder assets for the Docker container.
This creates basic placeholder files that can be used as defaults.
"""

import os
import wave
import struct
from PIL import Image
import numpy as np


def create_tone(filename, frequency, duration, sample_rate=22050):
    """Create a simple tone and save it as a WAV file."""
    frames = []
    for i in range(int(duration * sample_rate)):
        value = int(16383 * np.sin(2 * np.pi * frequency * i / sample_rate))
        frames.append(struct.pack('<h', value))
    
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(frames))


def main():
    """Create all placeholder assets."""
    # Create placeholder video directory
    os.makedirs('/tmp/assets', exist_ok=True)
    
    # Create a simple black image that moviepy can use
    img = Image.new('RGB', (1280, 720), color='black')
    img.save('/tmp/assets/placeholder.jpg')
    
    # Create music directory
    os.makedirs('/tmp/music', exist_ok=True)
    
    # Create default audio files with different tones
    create_tone('/tmp/music/default.wav', 440, 5)  # A4 note
    create_tone('/tmp/music/upbeat_default.wav', 523, 5)  # C5 note
    create_tone('/tmp/music/calm_default.wav', 349, 5)  # F4 note
    create_tone('/tmp/music/sad_default.wav', 294, 5)  # D4 note
    
    print("Placeholder assets created successfully!")


if __name__ == "__main__":
    main()
