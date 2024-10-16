import os
import tempfile
from typing import Any, Dict, List

from langchain.docstore.document import Document
from moviepy.video.io.VideoFileClip import VideoFileClip

from backend.logger import logger
from backend.modules.parsers.audio_parser import AudioParser
from backend.modules.parsers.multi_modal_parser import MultiModalParser
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
                "prompt": "Descibe the given information present in the image - textual/charts/graphs/tables in detail.",
                "total_frames": 15, // total images to be process from video, for testing puposes, if not provided all the images will be processed
                "fps": 0.2 // configure this for controlling frame rate.
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
        fps: float = 0.2,
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
        self.fps = fps  # configure this for controlling frame rate.

        super().__init__(**kwargs)

    def _get_images_from_video(self, video_filepath: str, temp_images_dir: str) -> str:
        """
        Extract images from video frames,
        We extract 1 frame every 5 seconds of the video
        Save all the images in temporary directory
        """
        file_name = os.path.basename(video_filepath)
        file_name_without_extension, _ = os.path.splitext(file_name)
        clip = VideoFileClip(video_filepath)
        clip.write_images_sequence(
            os.path.join(
                temp_images_dir, file_name_without_extension + "_frame%04d.png"
            ),
            fps=self.fps,
        )

    def _get_audio_from_video(self, video_filepath: str, temp_audio_dir: str) -> str:
        """
        Extract audio from video
        """
        file_name = os.path.basename(video_filepath)
        clip = VideoFileClip(video_filepath)
        clip.audio.write_audiofile(os.path.join(temp_audio_dir, file_name + ".wav"))

    async def get_chunks(
        self, filepath: str, metadata: Dict[Any, Any] | None, **kwargs
    ) -> List[Document]:
        """
        Get the chunks of the video file.
        """
        with tempfile.TemporaryDirectory(suffix="") as directory:
            try:
                # Extract images from video
                temp_images_dir = os.path.join(directory, "images")
                os.makedirs(temp_images_dir, exist_ok=True)
                self._get_images_from_video(filepath, temp_images_dir)

                # Init multimodal parser for extracting text from images
                multimodal_parser = MultiModalParser(
                    model_configuration=self.vlm_model_configuration, prompt=self.prompt
                )

                # Iterate over all the images and extract text from them
                parsed_video_text = []
                for idx, image in enumerate(os.listdir(temp_images_dir)):
                    image_path = os.path.join(temp_images_dir, image)
                    image_text = await multimodal_parser.get_chunks(
                        image_path, metadata
                    )
                    parsed_video_text.extend(image_text)
                    logger.info(
                        f"Extracted text from image: {image_text[0].page_content}"
                    )
                    if idx == self.total_frames:
                        break

                # Extact audio from video
                temp_audio_dir = os.path.join(directory, "audio")
                os.makedirs(temp_audio_dir, exist_ok=True)
                self._get_audio_from_video(filepath, temp_audio_dir)

                # Init audio parser for extracting text from audio
                audio_parser = AudioParser(
                    model_configuration=self.audio_model_configuration,
                    max_chunk_size=self.max_chunk_size,
                )

                # Extract text from audio
                audio_text = await audio_parser.get_chunks(
                    os.path.join(temp_audio_dir, os.listdir(temp_audio_dir)[0]),
                    metadata,
                )

                # Combine all the extracted text
                final_text = parsed_video_text + audio_text

                return final_text

            except Exception as e:
                logger.exception(f"Error in getting chunks: {e}")
                raise e
