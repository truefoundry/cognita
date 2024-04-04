import re
import deepdoctection as dd
import pandas as pd
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.modules.parsers.parser import BaseParser

config_overwrite = [
    "TEXT_ORDERING.INCLUDE_RESIDUAL_TEXT_CONTAINER=True",
    "USE_PDF_MINER=False",
    "SEGMENTATION.THRESHOLD_ROWS=0.8",
    "SEGMENTATION.THRESHOLD_COLS=0.8",
    "SEGMENTATION.REMOVE_IOU_THRESHOLD_ROWS=0.6",
    "SEGMENTATION.REMOVE_IOU_THRESHOLD_COLS=0.6",
    "PT.LAYOUT.WEIGHTS=microsoft/table-transformer-detection/pytorch_model.bin",
    "PT.LAYOUT.PAD.TOP=60",
    "PT.LAYOUT.PAD.RIGHT=60",
    "PT.LAYOUT.PAD.BOTTOM=60",
    "PT.LAYOUT.PAD.LEFT=60",
    "PT.ITEM.WEIGHTS=microsoft/table-transformer-structure-recognition/pytorch_model.bin",
    "PT.CELL.WEIGHTS=microsoft/table-transformer-structure-recognition/pytorch_model.bin",
    "PT.ITEM.FILTER=['table']",
    "USE_OCR=True",
    "OCR.USE_DOCTR=False",
    "OCR.USE_TESSERACT=True",
]


class CustomPdfParserUsingPyMuPDF(BaseParser):
    """
    PdfParserUsingPyMuPDF is a parser class for extracting text from PDF files using PyMuPDF library.
    """

    supported_file_extensions = [".pdf"]

    def __init__(self, max_chunk_size: int = 1024, *args, **kwargs):
        """
        Initializes the PdfParserUsingPyMuPDF object.
        """
        self.max_chunk_size = max_chunk_size

    async def get_chunks(self, filepath, metadata, *args, **kwargs):
        """
        Asynchronously extracts text from a PDF file and returns it in chunks.
        """
        print("Parsing file - " + str(filepath))
        analyzer = dd.get_dd_analyzer(
            reset_config_file=False, config_overwrite=config_overwrite
        )
        df = analyzer.analyze(path=filepath)
        df.reset_state()
        doc = iter(df)
        tables = []
        table_docs = []
        final_texts = []
        # try:
        for ix, page in enumerate(doc):
            tables = page.tables
            if len(tables) > 0:
                for table in tables:
                    table_data = table.csv
                    print(
                        "-----------------Table for page - "
                        + str(page.page_number)
                        + "---------------------"
                    )

                    table_data = pd.DataFrame(table_data)
                    # Table data is a pandas DataFrame, convert it to console string
                    table_data = table_data.to_string()
                    tab_doc = [
                        Document(
                            page_content=table_data,
                            metadata={
                                "page_num": page.page_number,
                                "type": "table",
                                "table_num": ix,
                            },
                        )
                    ]
                    table_docs.extend(tab_doc)

            text = page.text

            # clean up text for any problematic characters
            text = re.sub("\n", " ", text).strip()
            text = text.encode("ascii", errors="ignore").decode("ascii")
            text = re.sub(r"([^\w\s])\1{4,}", " ", text)
            text = re.sub(" +", " ", text).strip()

            # Create a Document object per page with page-specific metadata
            if len(text) > self.max_chunk_size:
                # Split the text into chunks of size less than or equal to max_chunk_size
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.max_chunk_size, chunk_overlap=200
                )
                text_splits = text_splitter.split_text(text)
                texts = [
                    Document(
                        page_content=text_split,
                        metadata={
                            "page_num": page.page_number,
                            "type": "text",
                        },
                    )
                    for text_split in text_splits
                ]
                final_texts.extend(texts)
            else:
                final_texts.append(
                    Document(
                        page_content=text,
                        metadata={
                            "page_num": page.page_number,
                            "type": "text",
                        },
                    )
                )
        # except Exception as ex:
        #     print(f"Error while parsing PDF file at {filepath}: {str(ex)}")
        #     # Return an empty list if there was an error during processing
        #     return []

        return final_texts + table_docs
