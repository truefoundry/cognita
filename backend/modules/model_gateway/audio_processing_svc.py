from typing import Optional

import aiofiles
import aiohttp


class AudioProcessingSvc:
    """
    Async Audio Processing Service that uses Faster-Whisper Server
    # Github: https://github.com/fedirz/faster-whisper-server
    """

    model: str
    base_url: str
    api_key: Optional[str] = None

    def __init__(self, *, base_url: str, model: str, api_key: Optional[str] = None):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
        self.data = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": "json",
            "language": "en",
            "timestamp_granularities": "segment",
            "stream": "true",
        }

    # allows class to be used as async context manager
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    # allows class to be used as async context manager
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_transcription(self, audio_file_path: str) -> aiohttp.ClientResponse:
        """
        Get streaming audio transcription from Faster-Whisper Server
        """
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        async with aiofiles.open(audio_file_path, "rb") as f:
            file_data = await f.read()

        data = aiohttp.FormData()
        data.add_field("file", file_data, filename="audio.wav")
        for key, value in self.data.items():
            data.add_field(key, str(value))

        headers = {"accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = await self.session.post(
            self.base_url.rstrip("/") + "/v1/audio/transcriptions",
            headers=headers,
            data=data,
        )
        response.raise_for_status()

        return response
