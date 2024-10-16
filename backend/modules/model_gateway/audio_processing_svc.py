from typing import AsyncIterator, Optional

import aiofiles
from aiohttp import ClientSession, FormData


class AudioProcessingSvc:
    """
    Async Audio Processing Service that uses Faster-Whisper Server
    # Github: https://github.com/fedirz/faster-whisper-server
    """

    def __init__(self, *, base_url: str, model: str, api_key: Optional[str] = None):
        """
        Initialize the AudioProcessingSvc.

        Args:
            base_url: The base URL of the Faster-Whisper Server.
            model: The model to use for transcription.
            api_key: Optional API key for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.transcription_url = f"{self.base_url}/v1/audio/transcriptions"
        self.default_params = self._get_default_params(model)

    @staticmethod
    def _get_default_params(model: str) -> dict:
        """
        Get default parameters for transcription.

        Args:
            model: The model to use for transcription.

        Returns:
            A dictionary of default parameters.
        """
        return {
            "model": model,
            "temperature": 0.1,
            "response_format": "json",
            "language": "en",
            "timestamp_granularities": "segment",
            "stream": "true",
        }

    async def _prepare_request_data(self, audio_file_path: str) -> FormData:
        """
        Prepare the request data for transcription.

        Args:
            audio_file_path: Path to the audio file.

        Returns:
            FormData object with file and parameters.
        """
        async with aiofiles.open(audio_file_path, "rb") as f:
            file_data = await f.read()

        data = FormData()
        data.add_field("file", file_data, filename="audio.wav")
        for key, value in self.default_params.items():
            data.add_field(key, str(value))

        return data

    def _get_headers(self) -> dict:
        """
        Get headers for the API request.

        Returns:
            A dictionary of headers.
        """
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_transcription(self, audio_file_path: str) -> AsyncIterator[str]:
        """
        Get streaming audio transcription from Faster-Whisper Server.

        Args:
            audio_file_path: Path to the audio file to transcribe.

        Yields:
            Transcription results as they become available.
        """
        async with ClientSession() as session:
            data = await self._prepare_request_data(audio_file_path)
            headers = self._get_headers()

            async with session.post(
                self.transcription_url,
                headers=headers,
                data=data,
            ) as response:
                response.raise_for_status()
                async for line in response.content:
                    line = line.strip()
                    if line:
                        yield line.decode("utf-8").split("data: ")[1]
