from typing import Optional, Sequence

import requests
from requests.adapters import HTTPAdapter, Retry

from backend.logger import logger


class AudioProcessingSvc:
    """
    Audio Processing Service that uses Faster-Whisper Server
    # Github: https://github.com/fedirz/faster-whisper-server
    """

    model: str
    base_url: str
    api_key: Optional[str] = None

    def __init__(self, *, base_url: str, model: str, api_key: Optional[str] = None):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.data = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": "json",
            "language": "en",
            "timestamp_granularities": "segment",
            "stream": "true",
        }
        self.retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        self.adapter = HTTPAdapter(max_retries=self.retry_strategy)
        self.session.mount("https://", self.adapter)
        self.session.mount("http://", self.adapter)

    def get_transcription(self, audio_file_path: str) -> str:
        """
        Get streaming audio transcription from Faster-Whisper Server
        """
        with open(audio_file_path, "rb") as f:
            files = {"file": f}
            headers = {"accept": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = self.session.post(
                self.base_url.rstrip("/") + "/transcribe",
                headers=headers,
                files=files,
                stream=True,
            )
            response.raise_for_status()

        return response
