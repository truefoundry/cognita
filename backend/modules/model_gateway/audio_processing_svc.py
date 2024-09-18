from typing import AsyncIterator, Optional

import aiofiles
import aiohttp


class AudioProcessingSvc:
    """
    Async Audio Processing Service that uses Faster-Whisper Server
    # Github: https://github.com/fedirz/faster-whisper-server
    """

    def __init__(self, *, base_url: str, model: str, api_key: Optional[str] = None):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.data = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": "json",
            "language": "en",
            "timestamp_granularities": "segment",
            "stream": "true",
        }

    async def get_transcription(self, audio_file_path: str) -> AsyncIterator[str]:
        """
        Get streaming audio transcription from Faster-Whisper Server
        """
        async with aiohttp.ClientSession() as session:
            async with aiofiles.open(audio_file_path, "rb") as f:
                file_data = await f.read()

            data = aiohttp.FormData()
            data.add_field("file", file_data, filename="audio.wav")
            for key, value in self.data.items():
                data.add_field(key, str(value))

            headers = {"accept": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with session.post(
                self.base_url.rstrip("/") + "/v1/audio/transcriptions",
                headers=headers,
                data=data,
            ) as response:
                response.raise_for_status()
                async for line in response.content:
                    line = line.strip()
                    if line:
                        yield line.decode("utf-8").split("data: ")[1]
