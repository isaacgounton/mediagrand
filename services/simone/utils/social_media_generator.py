from __future__ import annotations

import json
import logging
import requests

from services.simone.utils.prompts import get_social_media_prompt
from config import OPENAI_MODEL, OPENAI_BASE_URL


class SocialMediaGenerator:
    def __init__(self, api_key: str, transcription_filename: str):
        self.api_key = api_key
        self.transcription_filename = transcription_filename

    def generate_post(self, platform: str, **kwargs) -> str:
        with open(self.transcription_filename, "r", encoding="utf-8") as file:
            transcript_content = file.read()

        prompt = get_social_media_prompt(platform, transcript_content, **kwargs)

        response = requests.post(
            url=f"{OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8"
            },
            data=json.dumps(
                {
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                },
                ensure_ascii=False
            ),
        )

        try:
            response.raise_for_status()
            response_text = response.text
            response_dict = json.loads(response_text)
            social_media_post = response_dict["choices"][0]["message"]["content"]
            return social_media_post
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred during social media generation: {http_err} - Response: {response.text}")
            raise ValueError(f"API request failed: {response.text}") from http_err
        except json.JSONDecodeError as json_err:
            logging.error(f"JSON decode error during social media generation: {json_err} - Response: {response.text}")
            raise ValueError(f"Invalid JSON response from API: {response.text}") from json_err
        except KeyError as key_err:
            logging.error(f"KeyError during social media generation: {key_err} in API response. Full response: {response.text}")
            raise ValueError(f"Unexpected API response format: Missing key {key_err}. Full response: {response.text}") from key_err
        except Exception as e:
            logging.error(f"An unexpected error occurred during social media generation API call: {e} - Response: {response.text}")
            raise ValueError(f"An unexpected error occurred: {e}. Full response: {response.text}") from e
