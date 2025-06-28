from __future__ import annotations

import json
import logging # Added logging import

import requests
from config import OPENAI_MODEL, OPENAI_BASE_URL


class Blogger:
    def __init__(self, api_key, transcription_filename, output_filename):
        self.api_key = api_key
        self.transcription_filename = transcription_filename
        self.output_filename = output_filename

    def generate_blogpost(self):
        with open(self.transcription_filename, "r", encoding="utf-8") as file:
            content = file.read()

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
                        {
                            "role": "system",
                            "content": "Generate a blogpost for the provided content.",
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
            blogpost = response_dict["choices"][0]["message"]["content"]
            with open(self.output_filename, "w", encoding="utf-8") as file:
                file.write(blogpost)
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred during blogpost generation: {http_err} - Response: {response.text}")
            raise ValueError(f"API request failed: {response.text}") from http_err
        except json.JSONDecodeError as json_err:
            logging.error(f"JSON decode error during blogpost generation: {json_err} - Response: {response.text}")
            raise ValueError(f"Invalid JSON response from API: {response.text}") from json_err
        except KeyError as key_err:
            logging.error(f"KeyError during blogpost generation: {key_err} in API response. Full response: {response.text}")
            raise ValueError(f"Unexpected API response format: Missing key {key_err}. Full response: {response.text}") from key_err
        except Exception as e:
            logging.error(f"An unexpected error occurred during blogpost generation API call: {e} - Response: {response.text}")
            raise ValueError(f"An unexpected error occurred: {e}. Full response: {response.text}") from e
