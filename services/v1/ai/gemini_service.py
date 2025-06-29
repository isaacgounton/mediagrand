import os
import json
import logging
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
        self.model_name = "gemini-2.5-flash"
        
        # Viral-focused system instruction (copied from viral-shorts-creator)
        self.system_instruction = (
            "You are a creative and detail-oriented scriptwriter. Your task is to analyze the provided video (or its transcript) "
            "and generate an engaging, concise summary that captures the unique and bizarre elements of the video. "
            "Your output will serve as a script for video shorts, so focus on the following:\n\n"
            "• **Overview:** Provide a clear description of the main actions and events.\n"
            "• **Highlights:** Emphasize any unusual, surprising, or humorous moments.\n"
            "• **Tone:** Keep the language energetic, engaging, and suitable for short-form content.\n"
            "• **Brevity:** Be concise while ensuring the viewer understands what makes the video interesting.\n"
            "• **Audience Hook:** Include a captivating hook at the beginning to grab the viewer's attention.\n\n"
            "Make sure your script clearly outlines what is happening in the video and why it's worth watching.\n\n"
            "Return your response as JSON with exactly these fields: {\"hook\": \"your engaging hook\", \"script\": \"your main script content\"}"
        )
    
    def upload_video_for_analysis(self, video_path: str) -> Any:
        """Upload video file to Gemini for analysis using the new API"""
        try:
            logger.info(f"Uploading video to Gemini: {video_path}")
            uploaded_file = self.client.files.upload(file=video_path)
            logger.info(f"Video uploaded successfully with new API")
            return uploaded_file
        except Exception as e:
            logger.error(f"Failed to upload video to Gemini: {e}")
            raise Exception(f"Failed to upload video to Gemini: {e}")
    
    def generate_viral_script(self, uploaded_file: Any, context: str = "") -> Dict[str, str]:
        """Generate viral script from uploaded video with optional context"""
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
            
            # Parse the JSON response
            script_data = json.loads(script_json)
            
            # Validate required fields
            if 'hook' not in script_data or 'script' not in script_data:
                raise ValueError("Generated script missing required 'hook' or 'script' fields")
            
            logger.info(f"Generated hook: {script_data['hook'][:50]}...")
            logger.info(f"Generated script: {script_data['script'][:100]}...")
            
            return script_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Raw response: {response.text}")
            raise Exception(f"Failed to parse AI response: {e}")
        except Exception as e:
            logger.error(f"Failed to generate viral script: {e}")
            raise Exception(f"Failed to generate viral script: {e}")
    
    def generate_script_from_transcript(self, transcript: str, context: str = "") -> Dict[str, str]:
        """Generate viral script from transcript text (fallback when video upload fails)"""
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
            
            # Parse the JSON response
            script_data = json.loads(script_json)
            
            # Validate required fields
            if 'hook' not in script_data or 'script' not in script_data:
                raise ValueError("Generated script missing required 'hook' or 'script' fields")
            
            logger.info(f"Generated hook from transcript: {script_data['hook'][:50]}...")
            logger.info(f"Generated script from transcript: {script_data['script'][:100]}...")
            
            return script_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Raw response: {response.text}")
            raise Exception(f"Failed to parse AI response: {e}")
        except Exception as e:
            logger.error(f"Failed to generate viral script from transcript: {e}")
            raise Exception(f"Failed to generate viral script from transcript: {e}")