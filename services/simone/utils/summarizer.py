from __future__ import annotations

import json
import logging # Added logging import

import requests


class Summarizer:
    def __init__(self, api_key, transcription_filename):
        self.api_key = api_key
        self.transcription_filename = transcription_filename

    def generate_summary(self):
        with open(self.transcription_filename, "r") as file:
            content = file.read()

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            data=json.dumps(
                {
                    "model": "google/gemma-3-12b-it:free",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Give top 3 important keywords for the provided content.",
                        },
                        {"role": "user", "content": content},
                    ],
                },
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
