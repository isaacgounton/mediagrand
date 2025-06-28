import os
import json
import logging
from typing import Dict, Optional, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        
        # Configuration for viral script generation (copied from viral-shorts-creator)
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "hook": {
                        "type": "string",
                    },
                    "script": {
                        "type": "string",
                    },
                },
                "required": ["hook", "script"],
            },
        }
        
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
            "Make sure your script clearly outlines what is happening in the video and why it's worth watching."
        )
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=self.generation_config,
            system_instruction=self.system_instruction
        )
    
    def upload_video_for_analysis(self, video_path: str) -> Any:
        """Upload video file to Gemini for analysis"""
        try:
            logger.info(f"Uploading video to Gemini: {video_path}")
            uploaded_file = genai.upload_file(path=video_path, display_name="Video for analysis")
            logger.info(f"Video uploaded successfully: {uploaded_file.uri}")
            return uploaded_file
        except Exception as e:
            logger.error(f"Failed to upload video to Gemini: {e}")
            raise Exception(f"Failed to upload video to Gemini: {e}")
    
    def generate_viral_script(self, uploaded_file: Any, context: str = "") -> Dict[str, str]:
        """Generate viral script from uploaded video with optional context"""
        try:
            logger.info("Generating viral script with Gemini AI")
            
            # Prepare the prompt parts
            prompt_parts = [
                {
                    "file_data": {
                        "mime_type": uploaded_file.mime_type,
                        "file_uri": uploaded_file.uri,
                    }
                }
            ]
            
            # Add context if provided
            if context.strip():
                prompt_parts.append({"text": f"Additional context: {context}"})
            
            # Generate content
            result = self.model.generate_content(prompt_parts)
            script_json = result.text
            
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
            logger.error(f"Raw response: {result.text}")
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
            
            result = self.model.generate_content(prompt)
            script_json = result.text
            
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
            logger.error(f"Raw response: {result.text}")
            raise Exception(f"Failed to parse AI response: {e}")
        except Exception as e:
            logger.error(f"Failed to generate viral script from transcript: {e}")
            raise Exception(f"Failed to generate viral script from transcript: {e}")