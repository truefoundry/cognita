import json
from typing import Any

import requests

from backend.logger import logger
from backend.settings import settings


class GPT4Vision:
    def __init__(self):
        self.TFY_LLM_GATEWAY_URL = settings.TFY_LLM_GATEWAY_URL
        self.TFY_API_KEY = settings.TFY_API_KEY
        self.client = self.TFY_LLM_GATEWAY_URL.strip("/") + "/openai/chat/completions"
        self.vision_model = "openai-main/gpt-4-turbo"
        self.summary_model = "openai-main/gpt-3-5-turbo"

    async def _send_request(self, payload):
        response = requests.post(
            self.TFY_LLM_GATEWAY_URL.rstrip("/") + "/openai/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.TFY_API_KEY}",
                # Set the tfy_log_request to "true" in X-TFY-METADATA header to log prompt and response for the request
                "X-TFY-METADATA": json.dumps(
                    {"tfy_log_request": "true", "Custom-Metadata": "Custom-Value"}
                ),
            },
            json=payload,
        )
        return response.json()

    async def __call__(
        self,
        base64_image: str,
        prompt: str = "Describe the information present in the image in a structured format.",
    ) -> Any:
        logger.debug(f"Processing Image...")
        payload = {
            "model": self.vision_model,
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
            "max_tokens": 2048,
        }

        response = await self._send_request(payload)
        if "choices" in response:
            return {"response": response["choices"][0]["message"]["content"]}
        if "error" in response:
            return {"error": response["error"]}

    async def summarize(self, text: str):
        logger.debug(f"Summarizing text...")
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "Generate a detailed summary of the given document.",
                },
                {"role": "user", "content": text},
            ],
            "model": self.summary_model,
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": ["</s>"],
        }

        response = await self._send_request(payload)
        if "choices" in response:
            output = response["choices"][0]["message"]["content"]
            return {"page_content": output}
        if "error" in response:
            return {"error": response["error"]}


if __name__ == "__main__":
    import asyncio

    gpt = GPT4Vision()
    output = asyncio.gather(
        gpt.summarize("The quick brown fox jumps over the lazy dog.")
    )
    print(output)
