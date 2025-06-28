import logging
from typing import Dict, Any
from PIL import Image, ImageOps
import requests
from io import BytesIO
import os
import uuid

from services.s3_toolkit import upload_to_s3
import os

# Configure logging
logger = logging.getLogger(__name__)

def image_overlay(params: Dict[str, Any]) -> str:
    """
    Process an image overlay request.
    
    Args:
        params: Job parameters including:
            - base_image_url: URL of the base image
            - overlay_images: List of overlay images with position information
            - output_format: Output image format (e.g., 'png', 'jpg', 'webp')
            - output_quality: Quality for lossy formats (1-100)
            - output_width: Width of the output image (optional)
            - output_height: Height of the output image (optional)
            - maintain_aspect_ratio: Whether to maintain aspect ratio when resizing
            
    Returns:
        The path to the output file
    """
    try:
        # Download base image
        response = requests.get(params["base_image_url"])
        response.raise_for_status()
        base_image = Image.open(BytesIO(response.content)).convert("RGBA")
        
        # Resize base image if needed
        if params.get("output_width") or params.get("output_height"):
            output_size = (
                params.get("output_width", base_image.width),
                params.get("output_height", base_image.height)
            )
            if params.get("maintain_aspect_ratio", True):
                base_image.thumbnail(output_size, Image.Resampling.LANCZOS)
            else:
                base_image = base_image.resize(output_size, Image.Resampling.LANCZOS)

        # Process overlays
        for overlay_info in sorted(params["overlay_images"], key=lambda o: o.get("z_index", 0)):
            # Download overlay image
            response = requests.get(overlay_info["url"])
            response.raise_for_status()
            overlay_image = Image.open(BytesIO(response.content)).convert("RGBA")
            
            # Apply opacity
            if "opacity" in overlay_info:
                alpha = int(overlay_info["opacity"] * 255)
                overlay_image.putalpha(alpha)
            
            # Apply rotation
            if "rotation" in overlay_info:
                overlay_image = overlay_image.rotate(overlay_info["rotation"], expand=True, resample=Image.Resampling.BICUBIC)
            
            # Resize overlay
            overlay_width = int(base_image.width * overlay_info.get("width", 0.2))
            overlay_height = int(base_image.height * overlay_info.get("height", 0.2))
            overlay_image.thumbnail((overlay_width, overlay_height), Image.Resampling.LANCZOS)
            
            # Position overlay
            x = int(base_image.width * overlay_info["x"])
            y = int(base_image.height * overlay_info["y"])
            
            # Paste overlay onto base image
            base_image.paste(overlay_image, (x, y), overlay_image)
            
        # Save result to a temporary file
        output_format = params.get("output_format", "png")
        output_quality = params.get("output_quality", 90)
        
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate a unique filename
        job_id = str(uuid.uuid4())
        output_filename = f"{job_id}.{output_format}"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Save the image
        base_image.save(
            output_path, 
            format=output_format.upper(), 
            quality=output_quality
        )
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error processing image overlay: {e}", exc_info=True)
        raise
