import json
import tempfile
from typing import Any, Dict, List

from langchain.docstore.document import Document

from backend.logger import logger
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.parsers.parser import BaseParser
from backend.modules.parsers.unstructured_io import UnstructuredIoParser
from backend.types import ModelConfig


class AudioParser(BaseParser):
    """
    AudioParser is a parser class for extracting text from audio input.
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

    def __init__(self, *, model_configuration: ModelConfig = None, **kwargs):
        """
        Initializes the AudioParser object.
        """
        self.model_configuration = model_configuration
        self.max_chunk_size = self.model_configuration.parameters.get(
            "max_chunk_size", 2000
        )
        self.audio_processing_svc = model_gateway.get_audio_model_from_model_config(
            model_name=self.model_configuration.name
        )

    async def get_chunks(
        self, filepath: str, metadata: Dict[Any, Any] | None, **kwargs
    ) -> List[Document]:
        """
        Get the chunks of the audio file.
        """
        try:
            parsed_audio_text = []

            response = self.audio_processing_svc.get_transcription(filepath=filepath)

            try:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8").split("data: ")[1])
                        parsed_audio_text.append(data)
                        logger.info(f"Transcription: {data}")
            except Exception as e:
                logger.error(f"Error in getting transcription: {e}")
                raise e

            combined_audio_text = " ".join(parsed_audio_text)

            # Save combined audio text to a temporary file
            with tempfile.NamedTemporaryFile(mode="w") as f:
                f.write(combined_audio_text)
                temp_filepath = f.name

                # Split the text into chunks
                unstructured_io_parser = UnstructuredIoParser(
                    max_chunk_size=self.max_chunk_size
                )

                final_texts = await unstructured_io_parser.get_chunks(
                    filepath=temp_filepath, metadata=metadata
                )

            return final_texts

        except Exception as e:
            logger.error(f"Error in getting chunks: {e}")
            raise e
