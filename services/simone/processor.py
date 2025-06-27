from __future__ import annotations

import os
import sys
import tempfile
import shutil
from typing import Optional
import uuid 
import mimetypes # Import mimetypes for content type guessing

from .utils.blogger import Blogger
from .utils.downloader import Downloader
from .utils.framer import Framer
from .utils.saver import Saver
from .utils.scorer import Scorer
from .utils.summarizer import Summarizer
from .utils.transcriber import Transcriber
from services.s3_toolkit import upload_to_s3 # Import S3 upload function


def process_video_to_blog(url: str, tesseract_path: str, gemma_api_key: str, cookies_content: Optional[str] = None, cookies_url: Optional[str] = None):
    if gemma_api_key:
        print("GEMMA 7B API key found. Continuing execution...")
    else:
        raise ValueError("Error: GEMMA 7B API key not found. Please provide an API key.")

    # S3 Configuration
    s3_url = os.environ.get("S3_ENDPOINT_URL")
    s3_access_key = os.environ.get("S3_ACCESS_KEY")
    s3_secret_key = os.environ.get("S3_SECRET_KEY")
    s3_bucket_name = os.environ.get("S3_BUCKET_NAME")
    s3_region = os.environ.get("S3_REGION")
    simone_upload_to_s3 = os.environ.get("SIMONE_UPLOAD_TO_S3", "false").lower() == "true"

    use_s3 = (
        simone_upload_to_s3
        and s3_url and s3_access_key and s3_secret_key and s3_bucket_name and s3_region
    )

    output_dir_name = str(uuid.uuid4())
    local_permanent_output_path = os.path.join(os.getcwd(), 'public', 'simone_outputs', output_dir_name)
    
    # Create a temporary directory for processing files
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Processing in temporary directory: {tmpdir}")
        original_cwd = os.getcwd()
        os.chdir(tmpdir) # Change to temporary directory

        try:
            print("Downloading audio and video...")
            downloads = Downloader(f"{url}", cookies_content, cookies_url)
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
            # Save to temporary directory first, then move/upload
            temp_output_for_saver = os.path.join(tmpdir, "simone_saver_outputs")
            os.makedirs(temp_output_for_saver, exist_ok=True)
            save = Saver(frame, score, temp_output_for_saver)
            save.save_best_frames()

            print("Blog post and screenshots have been generated!")

            blog_post_content = ""
            with open("generated_blogpost.txt", "r") as f:
                blog_post_content = f.read()
            
            output_blog_post_url = ""
            output_screenshot_urls = []

            if use_s3:
                print("Uploading outputs to S3...")
                try:
                    # Upload blog post
                    blog_post_s3_key = f"simone_outputs/{output_dir_name}/generated_blogpost.txt"
                    output_blog_post_url = upload_to_s3(
                        file_path="generated_blogpost.txt",
                        s3_url=s3_url,
                        access_key=s3_access_key,
                        secret_key=s3_secret_key,
                        bucket_name=s3_bucket_name,
                        region=s3_region,
                        content_type="text/plain"
                    )

                    # Upload screenshots
                    for f_name in os.listdir(temp_output_for_saver):
                        if f_name.startswith("screenshot_") and f_name.endswith(".png"):
                            file_path_to_upload = os.path.join(temp_output_for_saver, f_name)
                            s3_key = f"simone_outputs/{output_dir_name}/{f_name}"
                            screenshot_url = upload_to_s3(
                                file_path=file_path_to_upload,
                                s3_url=s3_url,
                                access_key=s3_access_key,
                                secret_key=s3_secret_key,
                                bucket_name=s3_bucket_name,
                                region=s3_region,
                                content_type=mimetypes.guess_type(f_name)[0] or "image/png"
                            )
                            output_screenshot_urls.append(screenshot_url)
                    print("Outputs uploaded to S3 successfully.")
                except Exception as e:
                    print(f"Failed to upload to S3: {e}. Falling back to local storage.")
                    use_s3 = False # Fallback to local storage

            if not use_s3:
                print("Saving outputs to local storage...")
                os.makedirs(local_permanent_output_path, exist_ok=True)
                # Copy blog post
                shutil.copy("generated_blogpost.txt", local_permanent_output_path)
                output_blog_post_url = f"/public/simone_outputs/{output_dir_name}/generated_blogpost.txt"

                # Copy screenshots
                for f_name in os.listdir(temp_output_for_saver):
                    if f_name.startswith("screenshot_") and f_name.endswith(".png"):
                        shutil.copy(os.path.join(temp_output_for_saver, f_name), local_permanent_output_path)
                        output_screenshot_urls.append(f"/public/simone_outputs/{output_dir_name}/{f_name}")
                print("Outputs saved to local storage successfully.")
            
            return {
                "blog_post_content": blog_post_content, # Still return content directly
                "blog_post_url": output_blog_post_url,
                "screenshots": output_screenshot_urls
            }

        finally:
            os.chdir(original_cwd) # Change back to original working directory
            # The temporary directory and its contents will be automatically cleaned up by `with tempfile.TemporaryDirectory()`.
