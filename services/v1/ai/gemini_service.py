import os
import json
import logging
import time
from typing import Dict, Optional, Any
from google import genai

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Set the API key as environment variable for the new client
        os.environ['GOOGLE_API_KEY'] = api_key
        self.client = genai.Client()
        
        # Model name for viral script generation
        self.model_name = "gemini-2.0-flash"
        
        # Viral-focused system instruction for clean narration text
        self.system_instruction = (
            "You are a voice-over scriptwriter creating narration text for viral short videos. "
            "Your task is to analyze the provided video (or its transcript) and generate clean, "
            "spoken narration that will be read by a text-to-speech system.\n\n"
            "IMPORTANT REQUIREMENTS:\n"
            "• Generate ONLY spoken text - no video directions, cuts, or production notes\n"
            "• No [brackets], **bold text**, or formatting - just clean narration\n"
            "• Write as if you're speaking directly to the viewer\n"
            "• Keep it conversational, engaging, and energetic\n"
            "• Focus on the most interesting/shocking elements\n"
            "• Use natural speech patterns with appropriate pauses\n"
            "• Include relevant hashtags only at the very end\n\n"
            "STRUCTURE:\n"
            "• Hook: 1-2 sentences that grab attention immediately\n"
            "• Script: Main narration (60-90 seconds of speaking time)\n\n"
            "Return your response as JSON: {\"hook\": \"spoken hook text\", \"script\": \"clean spoken narration\"}"
        )
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean markdown-wrapped JSON response from AI model."""
        text = response_text.strip()
        
        # Remove markdown code fences if present
        if text.startswith('```json'):
            text = text[7:]  # Remove '```json'
        elif text.startswith('```'):
            text = text[3:]   # Remove '```'
        
        if text.endswith('```'):
            text = text[:-3]  # Remove trailing '```'
        
        return text.strip()
    
    def upload_video_for_analysis(self, video_path: str) -> Any:
        """Upload video file to Gemini for analysis using the new API"""
        try:
            logger.info(f"Uploading video to Gemini: {video_path}")
            uploaded_file = self.client.files.upload(file=video_path)
            logger.info(f"Video uploaded successfully with new API: {uploaded_file.uri}")
            
            # Wait for file to become ACTIVE
            logger.info("Waiting for file to become ACTIVE...")
            max_wait_time = 60  # Maximum wait time in seconds
            wait_interval = 2   # Check every 2 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                file_info = self.client.files.get(uploaded_file.name)
                logger.info(f"File state: {file_info.state}")
                
                if file_info.state == 'ACTIVE':
                    logger.info("File is now ACTIVE and ready for use")
                    return uploaded_file
                elif file_info.state == 'FAILED':
                    raise Exception(f"File upload failed with state: {file_info.state}")
                
                time.sleep(wait_interval)
                elapsed_time += wait_interval
            
            raise Exception(f"File did not become ACTIVE within {max_wait_time} seconds")
            
        except Exception as e:
            logger.error(f"Failed to upload video to Gemini: {e}")
            raise Exception(f"Failed to upload video to Gemini: {e}")
    
    def generate_viral_script(self, uploaded_file: Any, context: str = "") -> Dict[str, str]:
        """Generate viral script from uploaded video with optional context"""
        response = None
        try:
            logger.info("Generating viral script with Gemini AI")
            
            # Prepare the content list for new API
            content_parts = [uploaded_file]
            
            # Build the prompt
            prompt = self.system_instruction
            if context.strip():
                prompt += f"\n\nAdditional context: {context}"
            
            content_parts.append(prompt)
            
            # Generate content using new API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=content_parts
            )
            script_json = response.text
            
            logger.info(f"Generated script JSON: {script_json[:200]}...")
            
            # Clean and parse the JSON response
            cleaned_json = self._clean_json_response(script_json)
            script_data = json.loads(cleaned_json)
            
            # Validate required fields
            if 'hook' not in script_data or 'script' not in script_data:
                raise ValueError("Generated script missing required 'hook' or 'script' fields")
            
            logger.info(f"Generated hook: {script_data['hook'][:50]}...")
            logger.info(f"Generated script: {script_data['script'][:100]}...")
            
            return script_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            if response is not None:
                logger.error(f"Raw response: {response.text}")
            raise Exception(f"Failed to parse AI response: {e}")
        except Exception as e:
            logger.error(f"Failed to generate viral script: {e}")
            raise Exception(f"Failed to generate viral script: {e}")
    
    def generate_script_from_transcript(self, transcript: str, context: str = "") -> Dict[str, str]:
        """Generate viral script from transcript text (fallback when video upload fails)"""
        response = None
        try:
            logger.info("Generating viral script from transcript")
            
            prompt = f"""
            Based on this video transcript, generate an engaging viral script:
            
            TRANSCRIPT:
            {transcript}
            
            CONTEXT:
            {context if context.strip() else 'No additional context provided'}
            
            Generate a JSON response with 'hook' and 'script' fields following the system instructions.
            """
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            script_json = response.text
            
            logger.info(f"Generated script JSON from transcript: {script_json[:200]}...")
            
            # Clean and parse the JSON response  
            cleaned_json = self._clean_json_response(script_json)
            script_data = json.loads(cleaned_json)
            
            # Validate required fields
            if 'hook' not in script_data or 'script' not in script_data:
                raise ValueError("Generated script missing required 'hook' or 'script' fields")
            
            logger.info(f"Generated hook from transcript: {script_data['hook'][:50]}...")
            logger.info(f"Generated script from transcript: {script_data['script'][:100]}...")
            
            return script_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            if response is not None:
                logger.error(f"Raw response: {response.text}")
            raise Exception(f"Failed to parse AI response: {e}")
        except Exception as e:
            logger.error(f"Failed to generate viral script from transcript: {e}")
            raise Exception(f"Failed to generate viral script from transcript: {e}")