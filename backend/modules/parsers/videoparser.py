import json
import os
import tempfile
from typing import Any, Dict, List

from langchain.docstore.document import Document
from moviepy.video.io.VideoFileClip import VideoFileClip

from backend.logger import logger
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.parsers.audioparser import AudioParser
from backend.modules.parsers.multimodalparser import MultiModalParser
from backend.modules.parsers.parser import BaseParser
from backend.types import ModelConfig


class VideoParser(BaseParser):
    """
    VideoParser is a parser class for extracting text from video input.
    {
        ".mp4": {
            "name": "VideoParser",
            "parameters": {
                "vlm_model_configuration": {
                    "name" : "truefoundry/openai-main/gpt-4o-mini"
                },
                "audio_model_configuration": {
                    "name": "faster-whisper/Systran/faster-distil-whisper-large-v3"
                },
                "max_chunk_size": 2000,
                "prompt": "Descibe the given information present in the image - textual/charts/graphs/tables in detail."
                "total_frames": 15 // total images to be process from video, for testing puposes, if not provided all the images will be processed
            }
        }
    }
    """

    supported_file_extensions = [
        ".mp4",
        ".avi",
        ".mov",
        ".flv",
        ".wmv",
        ".webm",
        ".mkv",
        ".mpg",
        ".mpeg",
        ".ogv",
        ".3gp",
    ]

    def __init__(
        self,
        vlm_model_configuration: ModelConfig,
        audio_model_configuration: ModelConfig,
        max_chunk_size: int = 2000,
        prompt: str = "",
        total_frames: int = -1,
        **kwargs,
    ):
        """
        Initializes the VideoParser object.
        """

        self.vlm_model_configuration = ModelConfig.model_validate(
            vlm_model_configuration
        )
        self.audio_model_configuration = ModelConfig.model_validate(
            audio_model_configuration
        )
        self.max_chunk_size = max_chunk_size
        self.prompt = prompt
        self.total_frames = (
            total_frames  # total images to be process from video, for testing puposes
        )

        super().__init__(**kwargs)

    def _get_images_from_video(self, video_filepath: str) -> str:
        """
        Extract images from video frames,
        We extract 1 frame every 5 seconds of the video
        Save all the images in temporary directory
        """
        _, file_name = os.path.split(video_filepath)
        file_name, _ = os.path.splitext(file_name)
        clip = VideoFileClip(video_filepath)
        temp_images_dir = tempfile.mkdtemp()
        clip.write_images_sequence(
            os.path.join(temp_images_dir, file_name + "_frame%04d.png"),
            fps=0.2,  # configure this for controlling frame rate.
        )
        return temp_images_dir

    def _get_audio_from_video(self, video_filepath: str) -> str:
        """
        Extract audio from video
        """
        _, file_name = os.path.split(video_filepath)
        # Save the audio in a temporary directory
        temp_audio_dir = tempfile.mkdtemp()
        clip = VideoFileClip(video_filepath)
        clip.audio.write_audiofile(os.path.join(temp_audio_dir, file_name + ".wav"))
        return temp_audio_dir

    async def get_chunks(
        self, filepath: str, metadata: Dict[Any, Any] | None, **kwargs
    ) -> List[Document]:
        """
        Get the chunks of the video file.
        """
        try:
            # Extract images from video
            temp_images_dir = self._get_images_from_video(filepath)

            # Init multimodal parser for extracting text from images
            multimodal_parser = MultiModalParser(
                model_configuration=self.vlm_model_configuration, prompt=self.prompt
            )

            # Iterate over all the images and extract text from them
            parsed_video_text = []
            for idx, image in enumerate(os.listdir(temp_images_dir)):
                image_path = os.path.join(temp_images_dir, image)
                image_text = await multimodal_parser.get_chunks(image_path, metadata)
                parsed_video_text.extend(image_text)
                logger.info(f"Extracted text from image: {image_text[0].page_content}")
                if idx == self.total_frames:
                    break

            # Extact audio from video
            temp_audio_dir = self._get_audio_from_video(filepath)

            # Init audio parser for extracting text from audio
            audio_parser = AudioParser(
                model_configuration=self.audio_model_configuration,
                max_chunk_size=self.max_chunk_size,
            )

            # Extract text from audio
            audio_text = await audio_parser.get_chunks(
                os.path.join(temp_audio_dir, os.listdir(temp_audio_dir)[0]), metadata
            )

            # Combine all the extracted text
            final_text = parsed_video_text + audio_text

            # Remove temporary directories
            try:
                for temp_dir in [temp_images_dir, temp_audio_dir]:
                    for file in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, file))
                    os.rmdir(temp_dir)
                    logger.info(f"Removed temporary directory: {temp_dir}")
            except Exception as e:
                logger.exception(f"Error in removing temporary directories: {e}")

            return final_text

        except Exception as e:
            logger.exception(f"Error in getting chunks: {e}")
            raise e
