import os
from typing import Dict, Iterator, List

import markdownify
from bs4 import BeautifulSoup as Soup
from langchain.document_loaders.recursive_url_loader import RecursiveUrlLoader

from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint


class WebLoader(BaseDataLoader):
    """
    This loader handles web URLs
    """

    def _remove_empty_lines(self, text):
        lines = text.split("\n")
        non_empty_lines = [line for line in lines if line.strip() != ""]
        return "\n".join(non_empty_lines)

    def _remove_tags(self, html):
        # parse html content
        soup = Soup(html, "html.parser")

        for data in soup(["style", "script"]):
            # Remove tags
            data.decompose()

        # return data by retrieving the tag content
        content = " ".join([str(d) for d in soup])
        # Remove html tags
        if content.startswith("html"):
            content = content[5:]
        return content

    def load_data_point(
        self,
        data_source: DataSource,
        dest_dir: str,
        data_point: DataPoint,
    ) -> LoadedDataPoint:
        raise NotImplementedError("Method not implemented")

    def load_filtered_data_points_from_data_source(
        self,
        data_source: DataSource,
        dest_dir: str,
        existing_data_point_fqn_to_hash: Dict[str, str],
        batch_size: int,
        data_ingestion_mode: DataIngestionMode,
    ) -> Iterator[List[LoadedDataPoint]]:
        """
        Loads data from a web URL specified by the given source URI.
        """
        max_depth = data_source.metadata.get("max_depth", 2)
        print("WebLoader -> max_depth: ", max_depth)
        self.loader = RecursiveUrlLoader(
            url=data_source.uri,
            max_depth=max_depth,
            extractor=lambda x: self._remove_empty_lines(
                markdownify.markdownify(self._remove_tags(x))
            ),
        )
        webpages = self.loader.load()

        loaded_data_points: List[LoadedDataPoint] = []
        for i, doc in enumerate(webpages):
            title: str = doc.metadata.get("title")
            url: str = doc.metadata.get("source")
            if title is None or url is None:
                continue

            file_name = f"file_{i}.md"
            full_dest_path = os.path.join(dest_dir, file_name)

            with open(full_dest_path, "w") as f:
                f.write(doc.page_content)

            data_point = DataPoint(
                data_source_fqn=data_source.fqn,
                data_point_uri=url,
                data_point_hash=f"{os.path.getsize(full_dest_path)}",
            )

            # If the data ingestion mode is incremental, check if the data point already exists.
            if (
                data_ingestion_mode == DataIngestionMode.INCREMENTAL
                and existing_data_point_fqn_to_hash.get(data_point.data_point_fqn)
                and existing_data_point_fqn_to_hash.get(data_point.data_point_fqn)
                == data_point.data_point_hash
            ):
                continue

            loaded_data_points.append(
                LoadedDataPoint(
                    data_point_hash=data_point.data_point_hash,
                    data_point_uri=data_point.data_point_uri,
                    data_source_fqn=data_point.data_source_fqn,
                    local_filepath=full_dest_path,
                    file_extension=".md",
                )
            )
            if len(loaded_data_points) >= batch_size:
                yield loaded_data_points
                loaded_data_points.clear()
        yield loaded_data_points
