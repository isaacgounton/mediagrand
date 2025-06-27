from __future__ import annotations

import os
import sys
import tempfile
import shutil
from typing import Optional

from .utils.blogger import Blogger
from .utils.downloader import Downloader
from .utils.framer import Framer
from .utils.saver import Saver
from .utils.scorer import Scorer
from .utils.summarizer import Summarizer
from .utils.transcriber import Transcriber


def process_video_to_blog(url: str, tesseract_path: str, gemma_api_key: str):
    if gemma_api_key:
        print("GEMMA 7B API key found. Continuing execution...")
    else:
        raise ValueError("Error: GEMMA 7B API key not found. Please provide an API key.")

    # Create a temporary directory for processing files
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Processing in temporary directory: {tmpdir}")
        original_cwd = os.getcwd()
        os.chdir(tmpdir) # Change to temporary directory

        try:
            print("Downloading audio and video...")
            downloads = Downloader(f"{url}")
            downloads.audio()
            downloads.video()

            print("Transcribing audio...")
            transcription_file = Transcriber("audio.mp4")
            transcription_file.transcribe()

            print("Generating keywords...")
            keywords = Summarizer(gemma_api_key, "transcription.txt")
            keyword = keywords.generate_summary()

            print("Generating blog post...")
            blogpost = Blogger(gemma_api_key, "transcription.txt", "generated_blogpost.txt")
            blogpost.generate_blogpost()

            print("Scoring frames...")
            frames = Framer("video.mp4")
            frame = frames.get_video_frames()

            scores = Scorer(frame, keyword, f"{tesseract_path}")
            score = scores.score_frames()

            print("Saving screenshots...")
            save = Saver(frame, score)
            save.save_best_frames()

            print("Blog post and screenshots have been generated!")

            # Prepare results to be returned
            blog_post_content = ""
            with open("generated_blogpost.txt", "r") as f:
                blog_post_content = f.read()

            # Assuming screenshots are named screenshot_0.png, screenshot_1.png, etc.
            screenshot_paths = []
            for f_name in os.listdir("."):
                if f_name.startswith("screenshot_") and f_name.endswith(".png"):
                    screenshot_paths.append(os.path.join(tmpdir, f_name))
            
            # Move generated blog post and screenshots to a more permanent location if needed later
            # For now, just return their content/paths from the temporary directory
            
            return {
                "blog_post": blog_post_content,
                "screenshots": screenshot_paths # These paths are still within the temporary directory
            }

        finally:
            os.chdir(original_cwd) # Change back to original working directory
            # The temporary directory and its contents will be automatically cleaned up by `with tempfile.TemporaryDirectory()`.
