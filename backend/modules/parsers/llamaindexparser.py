from typing import Any, Dict, List

from langchain.docstore.document import Document
from llama_index.core.extractors import (
    BaseExtractor,
    KeywordExtractor,
    QuestionsAnsweredExtractor,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode

from backend.logger import logger
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.parsers.parser import BaseParser
from backend.types import ExtractorConfig, ModelConfig


class LlamaIndexParser(BaseParser):
    """Demo parser that uses llamaindex parsing and uses QuestionAnswer extractor under the hood
    {
        ".txt": {
            "name": "LlamaIndexParser",
            "parameters": {
                "max_chunk_size": 1024,
                "chunk_overlap": 20,
                "extractors": [
                    {
                        "name": "QuestionsAnsweredExtractor",
                        "parameters": {
                            "model_name": "truefoundry/openai-main/gpt-4o-mini",
                            "num_questions": 3
                        }
                    },
                    {
                        "name": "KeywordExtractor",
                        "parameters": {
                            "model_name": "truefoundry/openai-main/gpt-4o-mini",
                            "num_keywords": 5
                        }
                    }
                ]
            }
        }
    }
    """

    supported_file_extensions = [".txt"]

    def __init__(
        self,
        *,
        max_chunk_size: int = 2000,
        chunk_overlap: int = 20,
        extractors: List[ExtractorConfig],
        **kwargs,
    ):
        """
        Initializes the LlamaIndexParser object.
        """
        # self.model_configuration = ModelConfig.model_validate(model_configuration)
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.extractors: List[BaseExtractor] = self._create_extractor_list(extractors)
        super().__init__(**kwargs)

    def _create_extractor_list(
        self, extractors: List[ExtractorConfig]
    ) -> List[BaseExtractor]:
        """
        Create a list of extractor objects from the configuration.
        """
        extractors_list = []
        for extractor in extractors:
            extractor = ExtractorConfig.model_validate(extractor)
            if extractor.name == "QuestionsAnsweredExtractor":
                extractors_list.append(
                    QuestionsAnsweredExtractor(
                        # creating a model config object from the parameters to align with model gateway
                        llm=model_gateway.get_llm_from_model_config(
                            ModelConfig(name=extractor.parameters["model_name"]),
                            library="llama-index",
                        ),
                        questions=extractor.parameters["num_questions"],
                    )
                )
            elif extractor.name == "KeywordExtractor":
                extractors_list.append(
                    KeywordExtractor(
                        # creating a model config object from the parameters to align with model gateway
                        llm=model_gateway.get_llm_from_model_config(
                            ModelConfig(name=extractor.parameters["model_name"]),
                            library="llama-index",
                        ),
                        keywords=extractor.parameters["num_keywords"],
                    )
                )
        return extractors_list

    async def get_chunks(
        self, filepath: str, metadata: Dict[Any, Any] | None, **kwargs
    ) -> List[Document]:
        """
        Asynchronously extracts text from input and returns it in chunks.
        """
        final_texts = []
        if metadata is None:
            metadata = {}

        with open(filepath, "r") as file:
            text = file.read()
            # Split text into sentences
            sentences = SentenceSplitter(
                chunk_size=self.max_chunk_size,
                chunk_overlap=self.chunk_overlap,
            ).split_text(text)

        for sentence in sentences:
            text_node = TextNode(
                text=sentence,
                metadata=metadata,
            )
            # Extract information from text nodes
            metadata_copy = metadata.copy()
            for extractor in self.extractors:
                try:
                    extracted_info = await extractor.aextract([text_node])
                    metadata_copy.update(extracted_info[0])

                except Exception as e:
                    logger.exception(f"Error extracting information: {e}")
            final_texts.append(Document(page_content=sentence, metadata=metadata_copy))

        return final_texts
