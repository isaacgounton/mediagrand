from __future__ import annotations

import json
import logging # Added logging import

import requests
from config import OPENAI_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL


class Summarizer:
    def __init__(self, api_key=None, transcription_filename=None, model=None, base_url=None):
        self.api_key = api_key or OPENAI_API_KEY
        self.transcription_filename = transcription_filename
        self.model = model or OPENAI_MODEL
        self.base_url = base_url or OPENAI_BASE_URL

        if not self.api_key:
            raise ValueError("API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")

    def generate_summary(self, system_prompt: str = "Give top 3 important keywords for the provided content."):
        if not self.transcription_filename:
            raise ValueError("Transcription filename is required for generate_summary method")

        with open(self.transcription_filename, "r", encoding="utf-8") as file:
            content = file.read()

        response = requests.post(
            url=f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8"
            },
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {"role": "user", "content": content},
                    ],
                },
                ensure_ascii=False
            ),
        )

        try:
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            response_text = response.text
            response_dict = json.loads(response_text)
            summary = response_dict["choices"][0]["message"]["content"]
            return summary
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
            raise ValueError(f"API request failed: {response.text}") from http_err
        except json.JSONDecodeError as json_err:
            logging.error(f"JSON decode error: {json_err} - Response: {response.text}")
            raise ValueError(f"Invalid JSON response from API: {response.text}") from json_err
        except KeyError as key_err:
            logging.error(f"KeyError: {key_err} in API response. Full response: {response.text}")
            raise ValueError(f"Unexpected API response format: Missing key {key_err}. Full response: {response.text}") from key_err
        except Exception as e:
            logging.error(f"An unexpected error occurred during API call: {e} - Response: {response.text}")
            raise ValueError(f"An unexpected error occurred: {e}. Full response: {response.text}") from e

    def generate_structured_script(self, context: str = ""):
        """Generate a structured script with hook and main content for viral shorts"""
        if not self.transcription_filename:
            raise ValueError("Transcription filename is required for generate_structured_script method")

        with open(self.transcription_filename, "r", encoding="utf-8") as file:
            content = file.read()

        system_prompt = """You are a creative and detail-oriented scriptwriter. Your task is to analyze the provided video transcript and generate an engaging, concise script that captures the unique and interesting elements of the content. Your output will serve as a script for video shorts, so focus on the following:

• Overview: Provide a clear description of the main actions and events.
• Highlights: Emphasize any unusual, surprising, or humorous moments.
• Tone: Keep the language energetic, engaging, and suitable for short-form content.
• Brevity: Be concise while ensuring the viewer understands what makes the content interesting.
• Audience Hook: Include a captivating hook at the beginning to grab the viewer's attention.

Return your response as a JSON object with two fields:
- "hook": A compelling opening line to grab attention (1-2 sentences)
- "script": The main script content that explains what's happening and why it's worth watching

Make sure your script clearly outlines what is happening in the video and why it's worth watching."""

        full_content = content
        if context.strip():
            full_content = f"Context: {context}\n\nTranscript: {content}"

        response = requests.post(
            url=f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8"
            },
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {"role": "user", "content": full_content},
                    ],
                },
                ensure_ascii=False
            ),
        )

        try:
            response.raise_for_status()
            response_text = response.text
            response_dict = json.loads(response_text)
            script_content = response_dict["choices"][0]["message"]["content"]

            # Try to parse as JSON first, if it fails, create a structured response
            try:
                script_json = json.loads(script_content)
                if "hook" in script_json and "script" in script_json:
                    return script_json
            except json.JSONDecodeError:
                pass

            # If not JSON or missing fields, create a structured response
            # Split the content into hook and script
            lines = script_content.strip().split('\n')
            if len(lines) >= 2:
                hook = lines[0].strip()
                script = '\n'.join(lines[1:]).strip()
            else:
                # If only one line, use first part as hook and rest as script
                words = script_content.split()
                if len(words) > 10:
                    hook = ' '.join(words[:10]) + "..."
                    script = script_content
                else:
                    hook = script_content
                    script = script_content

            return {
                "hook": hook,
                "script": script
            }

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
            raise ValueError(f"API request failed: {response.text}") from http_err
        except json.JSONDecodeError as json_err:
            logging.error(f"JSON decode error: {json_err} - Response: {response.text}")
            raise ValueError(f"Invalid JSON response from API: {response.text}") from json_err
        except KeyError as key_err:
            logging.error(f"KeyError: {key_err} in API response. Full response: {response.text}")
            raise ValueError(f"Unexpected API response format: Missing key {key_err}. Full response: {response.text}") from key_err
        except Exception as e:
            logging.error(f"An unexpected error occurred during API call: {e} - Response: {response.text}")
            raise ValueError(f"An unexpected error occurred: {e}. Full response: {response.text}") from e
