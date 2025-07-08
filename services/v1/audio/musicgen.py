import os
import tempfile
import logging
import uuid
from transformers import pipeline
import scipy.io.wavfile
import numpy as np
from services.cloud_storage import get_storage_provider
from services.ffmpeg_toolkit import convert_audio_format

class MusicGenService:
    """Service for generating music using Meta's MusicGen model"""
    
    def __init__(self):
        self.model_cache = {}
        self.temp_dir = os.environ.get('LOCAL_STORAGE_PATH', '/tmp')
        
    def _get_model(self, model_size="small"):
        """Get or load the MusicGen model with caching"""
        model_name = f"facebook/musicgen-{model_size}"
        
        if model_name not in self.model_cache:
            try:
                logging.info(f"Loading MusicGen model: {model_name}")
                self.model_cache[model_name] = pipeline(
                    "text-to-audio", 
                    model_name,
                    device=-1  # CPU usage
                )
                logging.info(f"Model {model_name} loaded successfully")
            except Exception as e:
                logging.error(f"Failed to load model {model_name}: {str(e)}")
                raise Exception(f"Failed to load MusicGen model: {str(e)}")
        
        return self.model_cache[model_name]
    
    def generate_music(self, description, duration=8, model_size="small", output_format="wav", job_id=None):
        """Generate music from text description"""
        try:
            # Get the model
            synthesizer = self._get_model(model_size)
            
            # Generate unique filename
            filename = f"musicgen_{job_id or uuid.uuid4().hex}"
            temp_wav_path = os.path.join(self.temp_dir, f"{filename}.wav")
            
            logging.info(f"Generating music for description: '{description}' (duration: {duration}s)")
            
            # Generate music
            music = synthesizer(description, forward_params={"max_new_tokens": duration * 50})
            
            # Save as WAV file
            sampling_rate = music["sampling_rate"]
            audio_data = music["audio"]
            
            # Ensure audio data is in the correct format
            if isinstance(audio_data, np.ndarray):
                # Normalize audio if needed
                if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                    audio_data = audio_data / np.max(np.abs(audio_data))
                
                # Convert to 16-bit PCM
                audio_data = (audio_data * 32767).astype(np.int16)
            
            # Save WAV file
            scipy.io.wavfile.write(temp_wav_path, rate=sampling_rate, data=audio_data)
            
            # Convert to requested format if needed
            if output_format.lower() == "mp3":
                output_path = os.path.join(self.temp_dir, f"{filename}.mp3")
                convert_audio_format(temp_wav_path, output_path, "mp3")
                os.remove(temp_wav_path)  # Clean up WAV file
            else:
                output_path = temp_wav_path
            
            # Upload to storage
            file_size = os.path.getsize(output_path)
            storage_provider = get_storage_provider()
            upload_result = storage_provider.upload_file(output_path, f"audio/{output_format}")
            
            # Create public URL (assuming S3-compatible storage)
            public_url = f"{os.getenv('S3_ENDPOINT_URL')}/{os.getenv('S3_BUCKET_NAME')}/{filename}.{output_format}"
            
            # Clean up temp file
            if os.path.exists(output_path):
                os.remove(output_path)
            
            # Calculate actual duration from generated audio
            actual_duration = len(audio_data) / sampling_rate
            
            return {
                "output_url": public_url,
                "duration": round(actual_duration, 2),
                "model_used": f"facebook/musicgen-{model_size}",
                "file_size": file_size,
                "sampling_rate": sampling_rate
            }
            
        except Exception as e:
            logging.error(f"MusicGen generation failed: {str(e)}", exc_info=True)
            raise Exception(f"Music generation failed: {str(e)}")
    
    def clear_cache(self):
        """Clear model cache to free memory"""
        self.model_cache.clear()
        logging.info("MusicGen model cache cleared")