import json
from typing import Any, Dict, List

import aiofiles
import aiofiles.os
from langchain.docstore.document import Document

from backend.logger import logger
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.parsers.parser import BaseParser
from backend.modules.parsers.unstructured_io import UnstructuredIoParser
from backend.types import ModelConfig


class AudioParser(BaseParser):
    """
    AudioParser is a parser class for extracting text from audio input.

    {
        ".mp3": {
            "name": "AudioParser",
            "parameters": {
                "model_configuration": {
                    "name" : "faster-whisper/Systran/faster-distil-whisper-large-v3"
                },
                "max_chunk_size": 2000
            }
        }
    }

    """

    supported_file_extensions = [
        ".flac",
        ".mp3",
        ".mp4",
        ".mpeg",
        ".mpga",
        ".m4a",
        ".ogg",
        ".wav",
        ".webm",
    ]

    def __init__(
        self, *, model_configuration: ModelConfig, max_chunk_size: int = 2000, **kwargs
    ):
        """
        Initializes the AudioParser object.
        """
        self.model_configuration = ModelConfig.model_validate(model_configuration)
        self.audio_processing_svc = model_gateway.get_audio_model_from_model_config(
            model_name=self.model_configuration.name
        )
        self.max_chunk_size = max_chunk_size
        super().__init__(**kwargs)

    async def get_chunks(
        self, filepath: str, metadata: Dict[Any, Any] | None, **kwargs
    ) -> List[Document]:
        """
        Get the chunks of the audio file.
        """
        try:
            parsed_audio_text = []

            async for line in self.audio_processing_svc.get_transcription(filepath):
                try:
                    data = json.loads(line)["text"]
                    parsed_audio_text.append(data)
                except json.JSONDecodeError:
                    logger.exception(f"Error decoding JSON: {line}")
                    raise json.JSONDecodeError
                except KeyError:
                    logger.exception(f"Missing 'text' key in JSON: {line}")
                    raise KeyError
                except Exception as e:
                    logger.exception(f"Error processing transcription line: {e}")
                    raise e

            combined_audio_text = " ".join(parsed_audio_text)
            logger.info(f"Total Combined audio text: {len(combined_audio_text)}")

            # Write the combined text to a '.txt' temporary file
            async with aiofiles.tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as temp_file:
                await temp_file.write(combined_audio_text)
                tempfile_name = temp_file.name

            # Split the text into chunks
            unstructured_io_parser = UnstructuredIoParser(
                max_chunk_size=self.max_chunk_size
            )

            final_texts = await unstructured_io_parser.get_chunks(
                filepath=tempfile_name, metadata=metadata
            )

            # Remove the temporary file
            try:
                await aiofiles.os.remove(tempfile_name)
                logger.info(f"Removed temporary file: {tempfile_name}")
            except Exception as e:
                logger.exception(f"Error in removing temporary file: {e}")

            return final_texts

        except Exception as e:
            logger.exception(f"Error in getting chunks: {e}")
            raise e
