import abc
import enum
import json
import logging
import warnings
from typing import Dict, List, Literal

import mlflow
import mlfoundry
from pydantic import BaseModel, Extra

from backend.modules.metadata_store.base import BaseMetadataStore
from backend.modules.metadata_store.models import (
    Collection, CollectionCreate, CollectionIndexerJobRun,
    CollectionIndexerJobRunCreate, CollectionIndexerJobRunStatus)
from backend.types import DataSource, EmbedderConfig, IndexingMode, ParserConfig
from backend.utils import _flatten, _unflatten

DEFAULT_CHUNK_SIZE = 500
CURRENT_INDEXER_JOB_RUN_NAME_KEY = "current_indexer_job_run_name"


class MLRunTypes(str, enum.Enum):
    COLLECTION = "COLLECTION"
    COLLECTION_INDEXER_JOB_RUN = "COLLECTION_INDEXER_JOB_RUN"


class BaseParams(abc.ABC, BaseModel):
    @abc.abstractmethod
    def to_mlfoundry_params(self):
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def from_mlfoundry_params(cls, params):
        raise NotImplementedError()


class CollectionMetadata(BaseParams):
    type: Literal[MLRunTypes.COLLECTION] = MLRunTypes.COLLECTION
    description: str | None = None
    embedder_config: EmbedderConfig
    chunk_size: int

    def to_mlfoundry_params(self) -> Dict[str, str]:
        data = self.dict().copy()
        data = _flatten(data, "embedder_config")
        for k, v in data.items():
            data[k] = json.dumps(v)
        return data

    @classmethod
    def from_mlfoundry_params(cls, params: Dict[str, str]):
        data = params.copy()
        for k, v in data.items():
            data[k] = json.loads(v)
        data = _unflatten(data, "embedder_config")
        return cls(**data)

    class Config:
        use_enum_values = True


class RunParams(BaseParams):
    type: Literal[
        MLRunTypes.COLLECTION_INDEXER_JOB_RUN
    ] = MLRunTypes.COLLECTION_INDEXER_JOB_RUN
    collection_name: str
    parser_config: ParserConfig
    data_source: DataSource
    indexing_mode: IndexingMode

    def to_mlfoundry_params(self) -> Dict[str, str]:
        data = self.dict().copy()
        data = _flatten(data, "data_source")
        data = _flatten(data, "parser_config")
        for k, v in data.items():
            data[k] = json.dumps(v)
        return data

    @classmethod
    def from_mlfoundry_params(cls, params: Dict[str, str]):
        data = params.copy()
        for k, v in data.items():
            data[k] = json.loads(v)
        data = _unflatten(data, "data_source")
        data = _unflatten(data, "parser_config")
        return cls(**data)

    class Config:
        use_enum_values = True


class Tags(BaseModel):
    type: MLRunTypes
    collection_name: str
    status: CollectionIndexerJobRunStatus = CollectionIndexerJobRunStatus.INITIALIZED

    class Config:
        use_enum_values = True
        extra = Extra.allow


class MLFoundry(BaseMetadataStore):
    ml_runs: dict[str, mlfoundry.MlFoundryRun] = {}

    def __init__(self, config: dict):
        self.ml_repo_name = config.get("ml_repo_name", None)
        if not self.ml_repo_name:
            raise Exception("config.ml_repo_name is not set.")
        logging.getLogger("mlfoundry").setLevel(logging.ERROR)
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        self.client = mlfoundry.get_client()
        self.client.create_ml_repo(self.ml_repo_name)

    def _get_run_by_name(self, run_name: str, no_cache: bool = False) -> mlfoundry.MlFoundryRun:
        """
        Cache the runs to avoid too many requests to the backend.
        """
        if len(self.ml_runs.keys()) > 50:
            self.ml_runs = {}
        if no_cache:
            self.ml_runs[run_name] = self.client.get_run_by_name(
                ml_repo=self.ml_repo_name, run_name=run_name
            )
        if run_name not in self.ml_runs:
            self.ml_runs[run_name] = self.client.get_run_by_name(
                ml_repo=self.ml_repo_name, run_name=run_name
            )
        return self.ml_runs.get(run_name)

    def create_collection(self, collection: CollectionCreate) -> Collection:
        created_collection = self.client.create_run(
            ml_repo=self.ml_repo_name,
            run_name=collection.name,
            tags=Tags(
                type=MLRunTypes.COLLECTION,
                collection_name=collection.name,
            ).dict(),
        )
        created_collection.log_params(
            param_dict=CollectionMetadata(
                description=collection.description,
                embedder_config=collection.embedder_config,
                chunk_size=collection.chunk_size,
            ).to_mlfoundry_params()
        )
        created_collection.end()
        return Collection(
            name=collection.name,
            description=collection.description,
            embedder_config=collection.embedder_config,
            chunk_size=collection.chunk_size,
        )

    def get_collection_by_name(
        self, collection_name: str, include_runs=False
    ) -> Collection:
        try:
            ml_run = self._get_run_by_name(run_name=collection_name, no_cache=True)
        except mlflow.exceptions.RestException as exp:
            if exp.error_code == "RESOURCE_DOES_NOT_EXIST":
                return None
        collection_params = CollectionMetadata.from_mlfoundry_params(
            params=ml_run.get_params()
        )
        collection = Collection(
            name=ml_run.run_name,
            description=collection_params.description,
            embedder_config=collection_params.embedder_config,
            chunk_size=collection_params.chunk_size,
        )
        if include_runs:
            collection.indexer_job_runs = self.get_collection_indexer_job_runs(
                collection_name=ml_run.run_name
            )
        return collection

    def get_collections(
        self, names: List[str] = None, include_runs=False
    ) -> List[Collection]:
        ml_runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.type = '{MLRunTypes.COLLECTION.value}'",
        )
        collections = []
        for ml_run in ml_runs:
            if names is not None and ml_run.run_name not in names:
                continue
            collection_params = CollectionMetadata.from_mlfoundry_params(
                params=ml_run.get_params()
            )
            collection = Collection(
                name=ml_run.run_name,
                description=collection_params.description,
                embedder_config=collection_params.embedder_config,
                chunk_size=collection_params.chunk_size,
            )
            if include_runs:
                collection.indexer_job_runs = self.get_collection_indexer_job_runs(
                    collection_name=ml_run.run_name
                )
            collections.append(collection)

        return collections

    def get_current_indexer_job_run(
        self, collection_name: str
    ) -> CollectionIndexerJobRun:
        collection = self._get_run_by_name(run_name=collection_name)
        tags = collection.get_tags(no_cache=True)
        current_indexer_job_run_name = tags.get(CURRENT_INDEXER_JOB_RUN_NAME_KEY, None)
        if current_indexer_job_run_name:
            return self.get_collection_indexer_job_run(
                collection_inderer_job_run_name=current_indexer_job_run_name
            )
        return None

    def get_collection_indexer_job_run(
        self, collection_inderer_job_run_name: str
    ) -> CollectionIndexerJobRun:
        try:
            run = self._get_run_by_name(
                run_name=collection_inderer_job_run_name, no_cache=True
            )
        except mlflow.exceptions.RestException as exp:
            if exp.error_code == "RESOURCE_DOES_NOT_EXIST":
                return None
        collection_inderer_job_run = RunParams.from_mlfoundry_params(
            params=run.get_params()
        )
        return CollectionIndexerJobRun(
            name=run.run_name,
            parser_config=collection_inderer_job_run.parser_config,
            data_source=collection_inderer_job_run.data_source,
            indexing_mode=collection_inderer_job_run.indexing_mode,
            status=CollectionIndexerJobRunStatus[
                run.get_tags(no_cache=True).get("status")
            ],
        )

    def get_collection_indexer_job_runs(self, collection_name: str):
        runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.type = '{MLRunTypes.COLLECTION_INDEXER_JOB_RUN.value}' and params.collection_name = '{collection_name}'",
        )
        indexer_job_runs = []
        for run in runs:
            collection_inderer_job_run = RunParams.from_mlfoundry_params(
                params=run.get_params()
            )
            indexer_job_runs.append(
                CollectionIndexerJobRun(
                    name=run.run_name,
                    parser_config=collection_inderer_job_run.parser_config,
                    data_source=collection_inderer_job_run.data_source,
                    indexing_mode=collection_inderer_job_run.indexing_mode,
                    status=CollectionIndexerJobRunStatus[
                        run.get_tags(no_cache=True).get("status")
                    ],
                )
            )
        return indexer_job_runs

    def create_collection_indexer_job_run(
        self, collection_name: str, indexer_job_run: CollectionIndexerJobRunCreate
    ) -> CollectionIndexerJobRun:
        collection = self._get_run_by_name(run_name=collection_name)
        created_run = self.client.create_run(
            ml_repo=self.ml_repo_name,
            run_name=collection_name,
            tags=Tags(
                type=MLRunTypes.COLLECTION_INDEXER_JOB_RUN,
                collection_name=collection_name,
                status=CollectionIndexerJobRunStatus.INITIALIZED,
            ).dict(),
        )
        created_run.log_params(
            param_dict=RunParams(
                collection_name=collection_name,
                parser_config=indexer_job_run.parser_config,
                data_source=indexer_job_run.data_source,
                indexing_mode=indexer_job_run.indexing_mode,
            ).to_mlfoundry_params()
        )
        collection.set_tags(
            tags={CURRENT_INDEXER_JOB_RUN_NAME_KEY: created_run.run_name}
        )
        return CollectionIndexerJobRun(
            name=created_run.run_name,
            data_source=indexer_job_run.data_source,
            parser_config=indexer_job_run.parser_config,
            indexing_mode=indexer_job_run.indexing_mode,
            status=CollectionIndexerJobRunStatus.INITIALIZED,
        )

    def delete_collection(self, collection_name: str, include_runs=False):
        if include_runs:
            collection_inderer_job_runs = self.client.search_runs(
                ml_repo=self.ml_repo_name,
                filter_string=f"params.type = '{MLRunTypes.COLLECTION_INDEXER_JOB_RUN.value}' and params.collection_name = '{collection_name}'",
            )
            for collection_inderer_job_run in collection_inderer_job_runs:
                collection_inderer_job_run.delete()
        collection = self._get_run_by_name(run_name=collection_name)
        collection.delete()

    def update_indexer_job_run_status(
        self,
        collection_inderer_job_run_name: str,
        status: CollectionIndexerJobRunStatus,
        extras: dict = None,
    ):
        collection_inderer_job_run = self._get_run_by_name(
            run_name=collection_inderer_job_run_name
        )
        collection_inderer_job_run.set_tags(
            {"status": status.value, **({**extras} if extras else {})}
        )
        if (
            status == CollectionIndexerJobRunStatus.COMPLETED
            or status == CollectionIndexerJobRunStatus.FAILED
        ):
            collection_inderer_job_run.end()

    def log_metrics_for_indexer_job_run(
        self,
        collection_inderer_job_run_name: str,
        metric_dict: dict[str, int | float],
        step: int = 0,
    ):
        collection_inderer_job_run = self._get_run_by_name(
            run_name=collection_inderer_job_run_name
        )
        collection_inderer_job_run.log_metrics(metric_dict=metric_dict, step=step)
