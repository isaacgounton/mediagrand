from __future__ import annotations

import os
import sys
import tempfile
import shutil
from typing import Optional, Dict, Any, List
import uuid 
import mimetypes # Import mimetypes for content type guessing
import json

from .utils.blogger import Blogger
from .utils.downloader import Downloader
from .utils.framer import Framer
from .utils.saver import Saver
from .utils.scorer import Scorer
from .utils.summarizer import Summarizer
from .utils.transcriber import Transcriber
from .utils.social_media_generator import SocialMediaGenerator
from services.s3_toolkit import upload_to_s3 # Import S3 upload function


def process_video_to_blog(url: str, tesseract_path: str, platform: Optional[str] = None, cookies_content: Optional[str] = None, cookies_url: Optional[str] = None):
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Error: OPENAI_API_KEY environment variable not found. Please set the API key.")
    print("OpenAI API key found via environment variable. Continuing execution...")

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
            print("Downloading audio and video using Simone Downloader...")
            downloader = Downloader(url=url, cookies_content=cookies_content, cookies_url=cookies_url)
            
            # Download video
            print("Downloading video...")
            downloader.video()
            if not os.path.exists("video.mp4"):
                raise Exception("Simone Downloader failed to create video.mp4")
            print("Video downloaded successfully.")

            # Download audio
            print("Downloading audio...")
            downloader.audio()
            if not os.path.exists("audio.mp4"):
                raise Exception("Simone Downloader failed to create audio.mp4")
            print("Audio downloaded successfully.")

            print("Audio and video downloaded successfully using Simone Downloader.")

            print("Transcribing audio...")
            transcription_file = Transcriber("audio.mp4")
            transcription_file.transcribe()

            print("Generating keywords...")
            keywords = Summarizer(api_key=openai_api_key, transcription_filename="transcription.txt")
            keyword = keywords.generate_summary()

            print("Generating blog post...")
            blogpost = Blogger(openai_api_key, "transcription.txt", "generated_blogpost.txt")
            blogpost.generate_blogpost()

            social_media_post_content = ""
            if platform:
                print(f"Generating social media post for {platform}...")
                social_media_generator = SocialMediaGenerator(openai_api_key, "transcription.txt")
                social_media_post_content = social_media_generator.generate_post(platform)
                print(f"Social media post for {platform} generated.")

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
            
            transcription_content = ""
            try:
                with open("transcription.txt", "r") as f:
                    transcription_content = f.read()
            except FileNotFoundError:
                transcription_content = ""
            
            output_blog_post_url = ""
            output_screenshot_urls = []
            output_transcription_url = ""

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
                    
                    # Upload transcription if available
                    if transcription_content and os.path.exists("transcription.txt"):
                        output_transcription_url = upload_to_s3(
                            file_path="transcription.txt",
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
                
                # Copy transcription if available
                if transcription_content and os.path.exists("transcription.txt"):
                    shutil.copy("transcription.txt", local_permanent_output_path)
                    output_transcription_url = f"/public/simone_outputs/{output_dir_name}/transcription.txt"

                # Copy screenshots
                for f_name in os.listdir(temp_output_for_saver):
                    if f_name.startswith("screenshot_") and f_name.endswith(".png"):
                        shutil.copy(os.path.join(temp_output_for_saver, f_name), local_permanent_output_path)
                        output_screenshot_urls.append(f"/public/simone_outputs/{output_dir_name}/{f_name}")
                print("Outputs saved to local storage successfully.")
            
            return {
                "blog_post_content": blog_post_content, # Still return content directly
                "blog_post_url": output_blog_post_url,
                "screenshots": output_screenshot_urls,
                "social_media_post_content": social_media_post_content,
                "transcription_content": transcription_content,
                "transcription_url": output_transcription_url
            }

        finally:
            os.chdir(original_cwd) # Change back to original working directory
            # The temporary directory and its contents will be automatically cleaned up by `with tempfile.TemporaryDirectory()`.


def process_video_with_enhanced_features(url: str, tesseract_path: str, 
                                        include_topics: bool = True,
                                        include_x_thread: bool = True,
                                        platforms: List[str] = None,
                                        thread_config: Dict[str, Any] = None,
                                        cookies_content: Optional[str] = None, 
                                        cookies_url: Optional[str] = None) -> Dict[str, Any]:
    """Enhanced video processing with topic identification and X thread generation."""
    
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Error: OPENAI_API_KEY environment variable not found. Please set the API key.")
    
    if platforms is None:
        platforms = ['x', 'linkedin', 'instagram']
    
    if thread_config is None:
        thread_config = {
            'max_posts': 8,
            'character_limit': 280,
            'thread_style': 'viral'
        }
    
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
        print(f"Enhanced processing in temporary directory: {tmpdir}")
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            print("Downloading audio and video using Simone Downloader...")
            downloader = Downloader(url=url, cookies_content=cookies_content, cookies_url=cookies_url)
            
            # Download video and audio
            print("Downloading video...")
            downloader.video()
            if not os.path.exists("video.mp4"):
                raise Exception("Simone Downloader failed to create video.mp4")
            
            print("Downloading audio...")
            downloader.audio()
            if not os.path.exists("audio.mp4"):
                raise Exception("Simone Downloader failed to create audio.mp4")
            
            print("Transcribing audio with enhanced features...")
            transcription_file = Transcriber("audio.mp4")
            transcription_file.transcribe()
            
            # Check for SRT file
            srt_filename = "transcription.srt" if os.path.exists("transcription.srt") else None
            
            print("Generating enhanced content with topics and threads...")
            # Initialize enhanced social media generator
            social_media_generator = SocialMediaGenerator(
                openai_api_key, 
                "transcription.txt",
                srt_filename
            )
            
            # Generate viral content package
            content_package = social_media_generator.generate_viral_content_package(
                platforms=platforms,
                include_topics=include_topics,
                include_thread=include_x_thread,
                **thread_config
            )
            
            # Generate traditional blog post
            print("Generating blog post...")
            blogpost = Blogger(openai_api_key, "transcription.txt", "generated_blogpost.txt")
            blogpost.generate_blogpost()
            
            # Generate keywords for frame scoring
            print("Generating keywords for frame analysis...")
            keywords = Summarizer(api_key=openai_api_key, transcription_filename="transcription.txt")
            keyword = keywords.generate_summary()
            
            # Process video frames
            print("Scoring frames...")
            frames = Framer("video.mp4")
            frame = frames.get_video_frames()
            
            scores = Scorer(frame, keyword, f"{tesseract_path}")
            score = scores.score_frames()
            
            print("Saving screenshots...")
            temp_output_for_saver = os.path.join(tmpdir, "simone_saver_outputs")
            os.makedirs(temp_output_for_saver, exist_ok=True)
            save = Saver(frame, score, temp_output_for_saver)
            save.save_best_frames()
            
            # Read blog post content
            blog_post_content = ""
            with open("generated_blogpost.txt", "r") as f:
                blog_post_content = f.read()
            
            # Read transcription content
            transcription_content = ""
            try:
                with open("transcription.txt", "r") as f:
                    transcription_content = f.read()
            except FileNotFoundError:
                transcription_content = ""
            
            # Handle file uploads/storage
            output_blog_post_url = ""
            output_screenshot_urls = []
            content_package_url = ""
            output_transcription_url = ""
            
            # Save content package to file
            content_package_filename = "viral_content_package.json"
            with open(content_package_filename, "w", encoding="utf-8") as f:
                json.dump(content_package, f, indent=2, ensure_ascii=False)
            
            if use_s3:
                print("Uploading enhanced outputs to S3...")
                try:
                    # Upload blog post
                    output_blog_post_url = upload_to_s3(
                        file_path="generated_blogpost.txt",
                        s3_url=s3_url,
                        access_key=s3_access_key,
                        secret_key=s3_secret_key,
                        bucket_name=s3_bucket_name,
                        region=s3_region,
                        content_type="text/plain"
                    )
                    
                    # Upload content package
                    content_package_url = upload_to_s3(
                        file_path=content_package_filename,
                        s3_url=s3_url,
                        access_key=s3_access_key,
                        secret_key=s3_secret_key,
                        bucket_name=s3_bucket_name,
                        region=s3_region,
                        content_type="application/json"
                    )
                    
                    # Upload transcription if available
                    if transcription_content and os.path.exists("transcription.txt"):
                        output_transcription_url = upload_to_s3(
                            file_path="transcription.txt",
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
                            screenshot_url = upload_to_s3(
                                file_path=file_path_to_upload,
                                s3_url=s3_url,
                                access_key=s3_access_key,
                                secret_key=s3_secret_key,
                                bucket_name=s3_bucket_name,
                                region=s3_region,
                                content_type="image/png"
                            )
                            output_screenshot_urls.append(screenshot_url)
                    
                    print("Enhanced outputs uploaded to S3 successfully.")
                except Exception as e:
                    print(f"Failed to upload to S3: {e}. Falling back to local storage.")
                    use_s3 = False
            
            if not use_s3:
                print("Saving enhanced outputs to local storage...")
                os.makedirs(local_permanent_output_path, exist_ok=True)
                
                # Copy blog post
                shutil.copy("generated_blogpost.txt", local_permanent_output_path)
                output_blog_post_url = f"/public/simone_outputs/{output_dir_name}/generated_blogpost.txt"
                
                # Copy content package
                shutil.copy(content_package_filename, local_permanent_output_path)
                content_package_url = f"/public/simone_outputs/{output_dir_name}/viral_content_package.json"
                
                # Copy transcription if available
                if transcription_content and os.path.exists("transcription.txt"):
                    shutil.copy("transcription.txt", local_permanent_output_path)
                    output_transcription_url = f"/public/simone_outputs/{output_dir_name}/transcription.txt"
                
                # Copy screenshots
                for f_name in os.listdir(temp_output_for_saver):
                    if f_name.startswith("screenshot_") and f_name.endswith(".png"):
                        shutil.copy(os.path.join(temp_output_for_saver, f_name), local_permanent_output_path)
                        output_screenshot_urls.append(f"/public/simone_outputs/{output_dir_name}/{f_name}")
                
                print("Enhanced outputs saved to local storage successfully.")
            
            return {
                "blog_post_content": blog_post_content,
                "blog_post_url": output_blog_post_url,
                "screenshots": output_screenshot_urls,
                "viral_content_package": content_package,
                "content_package_url": content_package_url,
                "transcription_content": transcription_content,
                "transcription_url": output_transcription_url,
                "enhanced_features": {
                    "topics_included": include_topics,
                    "x_thread_included": include_x_thread,
                    "platforms_processed": platforms,
                    "thread_config": thread_config
                },
                "processing_summary": {
                    "total_topics": len(content_package.get('content', {}).get('topics', {}).get('topics', [])) if include_topics else 0,
                    "thread_posts": len(content_package.get('content', {}).get('x_thread', {}).get('thread', [])) if include_x_thread else 0,
                    "platforms_generated": list(content_package.get('content', {}).get('posts', {}).keys()),
                    "screenshots_count": len(output_screenshot_urls)
                }
            }

        finally:
            os.chdir(original_cwd)
            # Temporary directory cleanup handled automatically
