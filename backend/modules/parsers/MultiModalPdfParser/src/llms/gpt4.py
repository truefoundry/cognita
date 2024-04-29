import json
from typing import Any

import requests

from backend.settings import settings


class GPT4Vision:
    def __init__(self):
        self.TFY_LLM_GATEWAY_URL = settings.TFY_LLM_GATEWAY_URL
        self.TFY_API_KEY = settings.TFY_API_KEY
        self.OPENAI_API_KEY = settings.OPENAI_API_KEY

    async def __call__(
        self,
        base64_image: str,
        prompt: str = "Describe the information present in the image in a structured format.",
    ) -> Any:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
        }

        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 1024,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        )

        if "error" in response.json():
            return {"error": response.json()["error"]}

        if "choices" in response.json():
            return {"response": response.json()["choices"][0]["message"]["content"]}

    async def summarize(self, text: str):
        try:
            response = requests.post(
                self.TFY_LLM_GATEWAY_URL.rstrip("/") + "/openai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.TFY_API_KEY}",
                    # Set the tfy_log_request to "true" in X-TFY-METADATA header to log prompt and response for the request
                    "X-TFY-METADATA": json.dumps(
                        {"tfy_log_request": "true", "Custom-Metadata": "Custom-Value"}
                    ),
                },
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": "Generate a detailed summary of the given document.",
                        },
                        {"role": "user", "content": text},
                    ],
                    "model": "openai-main/gpt-3-5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "top_p": 0.9,
                    "top_k": 50,
                    "repetition_penalty": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                    "stop": ["</s>"],
                },
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_error:
            return {"error": f"HTTP error occurred: {http_error}"}

        data = response.json()
        output = data["choices"][0]["message"]["content"]
        return {"page_content": output}


if __name__ == "__main__":
    gpt = GPT4Vision()
    print(
        gpt.summarize(
            "The quick brown fox jumps over the lazy dog. And then the dog barks."
        )
    )
