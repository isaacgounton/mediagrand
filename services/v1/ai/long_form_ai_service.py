import os
import json
import logging
from typing import Dict, Optional, Any, List
import google.generativeai as genai

logger = logging.getLogger(__name__)

class LongFormAIService:
    """
    AI service specialized for long-form content generation
    Optimized for educational, commentary, and documentary-style videos
    """
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        
        # Configuration for long-form content generation
        self.generation_config = {
            "temperature": 0.8,  # Slightly more conservative than viral content
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 16384,  # Larger for long-form content
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "introduction": {"type": "string"},
                    "main_sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "content": {"type": "string"},
                                "duration_estimate": {"type": "number"}
                            },
                            "required": ["title", "content", "duration_estimate"]
                        }
                    },
                    "conclusion": {"type": "string"},
                    "total_duration_estimate": {"type": "number"}
                },
                "required": ["title", "introduction", "main_sections", "conclusion", "total_duration_estimate"],
            },
        }
    
    def get_system_instruction(self, content_style: str, target_duration: int) -> str:
        """Get system instruction based on content style and target duration"""
        
        base_instruction = (
            "You are a professional content creator specializing in long-form educational and commentary videos. "
            "Your task is to analyze the provided video content and create a comprehensive, engaging script that "
            "transforms the source material into well-structured long-form content suitable for YouTube."
        )
        
        style_instructions = {
            "educational": (
                "Focus on teaching and explaining concepts clearly. Structure content with:\n"
                "• Clear learning objectives and takeaways\n"
                "• Step-by-step explanations with examples\n"
                "• Logical flow from basic to advanced concepts\n"
                "• Engaging educational language that keeps viewers interested\n"
                "• Periodic summaries and knowledge checks"
            ),
            "commentary": (
                "Provide insightful analysis and commentary. Structure content with:\n"
                "• Context and background information\n"
                "• Multiple perspectives and viewpoints\n"
                "• Critical analysis of key moments\n"
                "• Personal insights and expert opinions\n"
                "• Thought-provoking questions and discussions"
            ),
            "documentary": (
                "Create a narrative documentary-style presentation. Structure content with:\n"
                "• Compelling storytelling with clear narrative arc\n"
                "• Historical context and background\n"
                "• Character development and human interest\n"
                "• Dramatic pacing and emotional engagement\n"
                "• Factual accuracy with engaging presentation"
            ),
            "analysis": (
                "Provide deep analytical breakdown. Structure content with:\n"
                "• Systematic examination of key elements\n"
                "• Data-driven insights and evidence\n"
                "• Comparative analysis and benchmarking\n"
                "• Professional evaluation and conclusions\n"
                "• Actionable insights and recommendations"
            )
        }
        
        duration_guidance = f"""
        Target Duration: {target_duration} seconds ({target_duration/60:.1f} minutes)
        
        Structure your content accordingly:
        • Introduction: 10-15% of total duration
        • Main sections: 70-80% of total duration (2-5 sections recommended)
        • Conclusion: 10-15% of total duration
        
        Ensure each section has enough content to fill its estimated duration while maintaining engagement.
        """
        
        style_specific = style_instructions.get(content_style, style_instructions["educational"])
        
        return f"{base_instruction}\n\n{style_specific}\n\n{duration_guidance}"
    
    def upload_video_for_analysis(self, video_path: str) -> Any:
        """Upload video file to Gemini for analysis"""
        try:
            logger.info(f"Uploading video to Gemini for long-form analysis: {video_path}")
            uploaded_file = genai.upload_file(path=video_path, display_name="Long-form video for analysis")
            logger.info(f"Video uploaded successfully: {uploaded_file.uri}")
            return uploaded_file
        except Exception as e:
            logger.error(f"Failed to upload video to Gemini: {e}")
            raise Exception(f"Failed to upload video to Gemini: {e}")
    
    def generate_long_form_script(self, 
                                uploaded_file: Any, 
                                content_style: str,
                                target_duration: int,
                                context: str = "",
                                script_tone: str = "professional") -> Dict[str, Any]:
        """Generate structured long-form script from uploaded video"""
        try:
            logger.info(f"Generating long-form script: style={content_style}, duration={target_duration}s")
            
            # Create model with appropriate system instruction
            system_instruction = self.get_system_instruction(content_style, target_duration)
            
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config=self.generation_config,
                system_instruction=system_instruction
            )
            
            # Prepare the prompt parts
            prompt_parts = [
                {
                    "file_data": {
                        "mime_type": uploaded_file.mime_type,
                        "file_uri": uploaded_file.uri,
                    }
                }
            ]
            
            # Build context prompt
            context_prompt = f"""
            Create a {content_style} script with a {script_tone} tone for this video content.
            Target duration: {target_duration} seconds ({target_duration/60:.1f} minutes)
            
            """
            
            if context.strip():
                context_prompt += f"Additional context: {context}\n\n"
            
            context_prompt += (
                "Analyze the video content thoroughly and create a structured script that:\n"
                "1. Has an engaging title that captures the essence\n"
                "2. Includes a compelling introduction that hooks viewers\n"
                "3. Breaks content into logical main sections with clear transitions\n"
                "4. Provides a satisfying conclusion that reinforces key points\n"
                "5. Estimates timing for each section to meet target duration\n\n"
                "Make the content engaging, informative, and well-paced for the target audience."
            )
            
            prompt_parts.append({"text": context_prompt})
            
            # Generate content
            result = model.generate_content(prompt_parts)
            script_json = result.text
            
            logger.info(f"Generated long-form script JSON: {script_json[:300]}...")
            
            # Parse the JSON response
            script_data = json.loads(script_json)
            
            # Validate required fields
            required_fields = ["title", "introduction", "main_sections", "conclusion", "total_duration_estimate"]
            for field in required_fields:
                if field not in script_data:
                    raise ValueError(f"Generated script missing required '{field}' field")
            
            logger.info(f"Generated title: {script_data['title']}")
            logger.info(f"Number of main sections: {len(script_data['main_sections'])}")
            logger.info(f"Estimated total duration: {script_data['total_duration_estimate']} seconds")
            
            return script_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Raw response: {result.text}")
            raise Exception(f"Failed to parse AI response: {e}")
        except Exception as e:
            logger.error(f"Failed to generate long-form script: {e}")
            raise Exception(f"Failed to generate long-form script: {e}")
    
    def generate_script_from_transcript(self, 
                                      transcript: str, 
                                      content_style: str,
                                      target_duration: int,
                                      context: str = "",
                                      script_tone: str = "professional") -> Dict[str, Any]:
        """Generate long-form script from transcript text (fallback when video upload fails)"""
        try:
            logger.info(f"Generating long-form script from transcript: style={content_style}")
            
            # Create model with appropriate system instruction
            system_instruction = self.get_system_instruction(content_style, target_duration)
            
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config=self.generation_config,
                system_instruction=system_instruction
            )
            
            prompt = f"""
            Based on this video transcript, create a {content_style} script with a {script_tone} tone.
            Target duration: {target_duration} seconds ({target_duration/60:.1f} minutes)
            
            TRANSCRIPT:
            {transcript}
            
            CONTEXT:
            {context if context.strip() else 'No additional context provided'}
            
            Analyze the transcript content and create a structured long-form script that transforms
            this material into engaging {content_style} content. Follow the system instructions
            for proper structure and timing.
            """
            
            result = model.generate_content(prompt)
            script_json = result.text
            
            logger.info(f"Generated long-form script from transcript: {script_json[:300]}...")
            
            # Parse the JSON response
            script_data = json.loads(script_json)
            
            # Validate required fields
            required_fields = ["title", "introduction", "main_sections", "conclusion", "total_duration_estimate"]
            for field in required_fields:
                if field not in script_data:
                    raise ValueError(f"Generated script missing required '{field}' field")
            
            logger.info(f"Generated title from transcript: {script_data['title']}")
            logger.info(f"Number of main sections: {len(script_data['main_sections'])}")
            logger.info(f"Estimated total duration: {script_data['total_duration_estimate']} seconds")
            
            return script_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Raw response: {result.text}")
            raise Exception(f"Failed to parse AI response: {e}")
        except Exception as e:
            logger.error(f"Failed to generate long-form script from transcript: {e}")
            raise Exception(f"Failed to generate long-form script from transcript: {e}")
    
    def combine_script_sections(self, script_data: Dict[str, Any]) -> str:
        """Combine all script sections into a single text for TTS"""
        try:
            # Start with introduction
            full_script = script_data['introduction']
            
            # Add main sections
            for section in script_data['main_sections']:
                full_script += f" {section['content']}"
            
            # Add conclusion
            full_script += f" {script_data['conclusion']}"
            
            return full_script.strip()
            
        except Exception as e:
            logger.error(f"Failed to combine script sections: {e}")
            raise Exception(f"Failed to combine script sections: {e}")