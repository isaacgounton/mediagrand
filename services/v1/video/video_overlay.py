import logging
import asyncio
from typing import Dict, Any
from PIL import Image, ImageOps
import requests
from io import BytesIO
import os
import uuid
import subprocess
import time

from services.s3_toolkit import upload_to_s3
import os

# Configure logging
logger = logging.getLogger(__name__)

def video_overlay(params: Dict[str, Any]) -> str:
    """
    Process a video overlay request.
    
    Args:
        params: Job parameters including:
            - base_image_url: URL of the base image
            - overlay_videos: List of overlay videos with position and timing information
            - output_duration: Duration of the output video (optional)
            - frame_rate: Frame rate of the output video
            - output_width: Width of the output video (optional)
            - output_height: Height of the output video (optional)
            - maintain_aspect_ratio: Whether to maintain aspect ratio when resizing
            - background_audio_url: URL of background audio (optional)
            - background_audio_volume: Volume for background audio
            
    Returns:
        The path to the output file
    """
    try:
        # Download base image
        response = requests.get(params["base_image_url"])
        response.raise_for_status()
        base_image = Image.open(BytesIO(response.content)).convert("RGBA")
        
        # Determine output dimensions
        output_width = params.get("output_width", base_image.width)
        output_height = params.get("output_height", base_image.height)
        
        # Create temporary directory
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create base image stream
        base_image_path = os.path.join(temp_dir, f"{job_id}_base.png")
        base_image.save(base_image_path)
        
        input_streams = [f"-loop 1 -t {params.get('output_duration', 10)} -i {base_image_path}"]
        filter_complex_parts = []
        overlay_inputs = []
        
        # Process each overlay video
        for i, overlay_info in enumerate(sorted(params["overlay_videos"], key=lambda o: o.get("z_index", 0))):
            overlay_video_path = os.path.join(temp_dir, f"{job_id}_overlay_{i}.mp4")
            
            # Download video
            video_response = requests.get(overlay_info["url"])
            video_response.raise_for_status()
            with open(overlay_video_path, "wb") as f:
                f.write(video_response.content)
            
            input_streams.append(f"-i {overlay_video_path}")
            overlay_inputs.append(f"[{i+1}:v]") # Video stream
            
            # Calculate position
            x_pos = int(output_width * overlay_info["x"])
            y_pos = int(output_height * overlay_info["y"])
            
            # Scale overlay video
            scale_filter = ""
            if "width" in overlay_info:
                overlay_width_pixels = int(output_width * overlay_info["width"])
                scale_filter = f"scale={overlay_width_pixels}:-1"
            elif "height" in overlay_info:
                overlay_height_pixels = int(output_height * overlay_info["height"])
                scale_filter = f"scale=-1:{overlay_height_pixels}"
            
            # Apply opacity and rotation
            alpha_filter = ""
            if "opacity" in overlay_info and overlay_info["opacity"] < 1.0:
                alpha_filter = f"format=yuva420p,colorchannelmixer=aa={overlay_info['opacity']}"
            
            rotate_filter = ""
            if "rotation" in overlay_info and overlay_info["rotation"] != 0:
                rotate_filter = f"rotate={overlay_info['rotation']}*PI/180:ow='rotw(iw)':oh='roth(ih)':c=black@0"
            
            # Combine filters
            vf_filters = ",".join(filter(None, [scale_filter, alpha_filter, rotate_filter]))
            if vf_filters:
                filter_complex_parts.append(f"[{i+1}:v]{vf_filters}[overlay_scaled_{i}]")
                overlay_inputs[-1] = f"[overlay_scaled_{i}]"
            
            # Overlay command
            filter_complex_parts.append(f"[base_video][{overlay_inputs[-1]}]overlay=x={x_pos}:y={y_pos}:enable='between(t,{overlay_info.get('start_time', 0)},{overlay_info.get('end_time', params.get('output_duration', 10))})'[base_video]")
        
        # Main filter for video overlays
        main_filter = ""
        if filter_complex_parts:
            # The initial [0:v] is the base image stream
            main_filter = f"[0:v]{filter_complex_parts[0]}"
            for part in filter_complex_parts[1:]:
                main_filter += f";{part}"
            main_filter += f"[final_video]"
        else:
            main_filter = "[0:v][final_video]" # No overlays, just base image
            
        # Background audio
        audio_inputs = []
        if params.get("background_audio_url"):
            background_audio_path = os.path.join(temp_dir, f"{job_id}_background_audio.mp3")
            audio_response = requests.get(params["background_audio_url"])
            audio_response.raise_for_status()
            with open(background_audio_path, "wb") as f:
                f.write(audio_response.content)
            input_streams.append(f"-i {background_audio_path}")
            audio_inputs.append(f"[{len(input_streams)-1}:a]volume={params.get('background_audio_volume', 0.2)}")
        
        # Combine audio streams
        audio_filter = ""
        if audio_inputs:
            audio_filter = f"{''.join(audio_inputs)}amix=inputs={len(audio_inputs)}[audio_out]"
            
        # Output filename
        output_filename = os.path.join(temp_dir, f"{job_id}_output.mp4")
        
        # FFmpeg command construction
        cmd = ["ffmpeg"]
        cmd.extend(input_streams)
        
        cmd.extend([
            "-filter_complex", f"{main_filter};{audio_filter}" if audio_filter else main_filter,
            "-map", "[final_video]",
        ])
        
        if audio_filter:
            cmd.extend(["-map", "[audio_out]"])
            
        cmd.extend([
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-movflags", "faststart",
            "-f", "mp4", output_filename
        ])
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        # Execute FFmpeg
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(process.stdout)
        logger.error(process.stderr)
        
        return output_filename
        
    except Exception as e:
        logger.error(f"Error processing video overlay: {e}", exc_info=True)
        raise
