from typing import Optional, Sequence

import aiohttp
import requests
from requests.adapters import HTTPAdapter, Retry


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

    # def get_transcription(self, audio_file_path: str) -> requests.Response:
    #     """
    #     Get streaming audio transcription from Faster-Whisper Server
    #     """
    #     with open(audio_file_path, "rb") as f:
    #         files = {"file": f}
    #         headers = {"accept": "application/json"}
    #         if self.api_key:
    #             headers["Authorization"] = f"Bearer {self.api_key}"
    #         response = self.session.post(
    #             self.base_url.rstrip("/") + "/v1/audio/transcriptions",
    #             headers=headers,
    #             data=self.data,
    #             files=files,
    #             stream=True,
    #         )
    #         response.raise_for_status()

    #     return response

    async def get_transcription(self, audio_file_path: str) -> aiohttp.ClientResponse:
        """
        Get streaming audio transcription from Faster-Whisper Server
        """
        async with aiohttp.ClientSession() as session:
            async with aiohttp.MultipartWriter("form-data") as mpwriter:
                with open(audio_file_path, "rb") as f:
                    part = mpwriter.append(f)
                    part.set_content_disposition(
                        "form-data", name="file", filename=audio_file_path
                    )

                headers = {"accept": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with session.post(
                    self.base_url.rstrip("/") + "/v1/audio/transcriptions",
                    headers=headers,
                    data=self.data,
                    data=mpwriter,
                    timeout=aiohttp.ClientTimeout(total=None),
                ) as response:
                    response.raise_for_status()
                    return response
