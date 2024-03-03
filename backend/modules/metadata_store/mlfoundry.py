import abc
import enum
import json
import logging
import warnings
from re import L
from typing import Any, Dict, List, Literal

import mlflow
import mlfoundry
from fastapi import HTTPException
from git import Optional
from pydantic import BaseModel

from backend.modules.metadata_store.base import BaseMetadataStore, get_data_source_fqn
from backend.types import (
    Collection,
    CreateCollection,
    CreateDataIngestionRun,
    CreateDataSource,
    DataIngestionMode,
    DataIngestionRun,
    DataIngestionRunStatus,
    DataSource,
    EmbedderConfig,
    ParserConfig,
)
from backend.utils import flatten, unflatten


class MLRunTypes(str, enum.Enum):
    COLLECTION = "COLLECTION"
    DATA_INGESTION_RUN = "DATA_INGESTION_RUN"
    DATA_SOURCE = "DATA_SOURCE"


class BaseParams(abc.ABC, BaseModel):

    @abc.abstractmethod
    def to_mlfoundry_params(self):
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def from_mlfoundry_params(cls, params):
        raise NotImplementedError()


class CollectionParams(BaseParams):
    entity_type: Literal[MLRunTypes.COLLECTION] = MLRunTypes.COLLECTION
    name: str
    description: Optional[str]
    embedder_config: EmbedderConfig

    def to_mlfoundry_params(self) -> Dict[str, str]:
        data = self.dict().copy()
        data = flatten(data, "embedder_config")
        for k, v in data.items():
            data[k] = json.dumps(v)
        return data

    @classmethod
    def from_mlfoundry_params(cls, params: Dict[str, str]):
        data = params.copy()
        for k, v in data.items():
            data[k] = json.loads(v)
        data = unflatten(data, "embedder_config")
        return cls(**data)

    class Config:
        use_enum_values = True


class DataSourceParams(BaseParams):
    entity_type: Literal[MLRunTypes.DATA_SOURCE] = MLRunTypes.DATA_SOURCE
    type: str
    uri: str
    fqn: str

    def to_mlfoundry_params(self) -> Dict[str, str]:
        data = self.dict().copy()
        for k, v in data.items():
            data[k] = json.dumps(v)
        return data

    @classmethod
    def from_mlfoundry_params(cls, params: Dict[str, str]):
        data = params.copy()
        for k, v in data.items():
            data[k] = json.loads(v)
        return cls(**data)

    class Config:
        use_enum_values = True


class DataIngestionRunParams(BaseParams):
    entity_type: Literal[MLRunTypes.DATA_INGESTION_RUN] = MLRunTypes.DATA_INGESTION_RUN
    collection_name: str
    data_source_fqn: str
    data_ingestion_mode: str
    parser_config: ParserConfig
    raise_error_on_failure: Optional[bool]

    def to_mlfoundry_params(self) -> Dict[str, str]:
        data = self.dict().copy()
        data = flatten(data, "parser_config")
        for k, v in data.items():
            data[k] = json.dumps(v)
        return data

    @classmethod
    def from_mlfoundry_params(cls, params: Dict[str, str]):
        data = params.copy()
        for k, v in data.items():
            data[k] = json.loads(v)
        data = unflatten(data, "parser_config")
        return cls(**data)

    class Config:
        use_enum_values = True


class BaseTags(BaseModel):

    @abc.abstractmethod
    def to_mlfoundry_tags(self):
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def from_mlfoundry_tags(cls, params):
        raise NotImplementedError()


class DataSourceTags(BaseTags):
    entity_type: Literal[MLRunTypes.DATA_SOURCE] = MLRunTypes.DATA_SOURCE
    metadata: Optional[Dict[str, Any]]

    def to_mlfoundry_tags(self) -> Dict[str, str]:
        data = self.dict().copy()
        data = flatten(data, "metadata")
        for k, v in data.items():
            if isinstance(v, str):
                data[k] = v
            data[k] = json.dumps(v)
        return data

    @classmethod
    def from_mlfoundry_tags(cls, params: Dict[str, str]):
        data = params.copy()
        for k, v in data.items():
            if k.startswith("mlf."):
                continue
            data[k] = json.loads(v)
        data = unflatten(data, "metadata")
        return cls(**data)

    class Config:
        use_enum_values = True


class DataIngestionRunTags(BaseTags):
    entity_type: Literal[MLRunTypes.DATA_INGESTION_RUN] = MLRunTypes.DATA_INGESTION_RUN
    collection_name: str
    data_source_fqn: str
    status: str

    def to_mlfoundry_tags(self) -> Dict[str, str]:
        data = self.dict().copy()
        for k, v in data.items():
            if isinstance(v, str):
                data[k] = v
            data[k] = json.dumps(v)
        return data

    @classmethod
    def from_mlfoundry_tags(cls, params: Dict[str, str]):
        data = params.copy()
        for k, v in data.items():
            if k.startswith("mlf."):
                continue
            data[k] = json.loads(v)
        return cls(**data)

    class Config:
        use_enum_values = True


class MLFoundry(BaseMetadataStore):
    ml_runs: dict[str, mlfoundry.MlFoundryRun] = {}
    CONSTANT_DATA_SOURCE_RUN_NAME = "tfy-datasource"

    def __init__(self, config: dict):
        self.ml_repo_name = config.get("ml_repo_name", None)
        if not self.ml_repo_name:
            raise Exception("config.ml_repo_name is not set.")
        logging.getLogger("mlfoundry").setLevel(logging.ERROR)
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        self.client = mlfoundry.get_client()
        self.client.create_ml_repo(self.ml_repo_name)

    def _get_run_by_name(
        self, run_name: str, no_cache: bool = False
    ) -> mlfoundry.MlFoundryRun | None:
        """
        Cache the runs to avoid too many requests to the backend.
        """
        try:
            if len(self.ml_runs.keys()) > 50:
                self.ml_runs = {}
            if no_cache:
                self.ml_runs[run_name] = self.client.get_run_by_name(
                    ml_repo=self.ml_repo_name, run_name=run_name
                )
            if run_name not in self.ml_runs.keys():
                self.ml_runs[run_name] = self.client.get_run_by_name(
                    ml_repo=self.ml_repo_name, run_name=run_name
                )
            return self.ml_runs.get(run_name)
        except mlflow.exceptions.RestException as exp:
            if exp.error_code == "RESOURCE_DOES_NOT_EXIST":
                return None
            raise exp

    def create_collection(self, collection: CreateCollection) -> Collection:
        existing_collection = self.get_collection_by_name(
            collection_name=collection.name
        )
        if existing_collection:
            raise HTTPException(
                status_code=400,
                detail=f"Collection with name {collection.name} already exists.",
            )
        created_collection = self.client.create_run(
            ml_repo=self.ml_repo_name,
            run_name=collection.name,
            tags={
                "entity_type": MLRunTypes.COLLECTION,
                "collection_name": collection.name,
            },
        )
        created_collection.log_params(
            param_dict=CollectionParams(
                name=collection.name,
                description=collection.description,
                embedder_config=collection.embedder_config,
            ).to_mlfoundry_params()
        )
        created_collection.end()
        return Collection(
            name=collection.name,
            description=collection.description,
            embedder_config=collection.embedder_config,
        )

    def get_collection_by_name(
        self, collection_name: str, no_cache: bool = False
    ) -> Collection | None:
        ml_run = self._get_run_by_name(run_name=collection_name, no_cache=no_cache)
        if not ml_run:
            return None
        collection_params = CollectionParams.from_mlfoundry_params(
            params=ml_run.get_params()
        )
        collection = Collection(
            name=ml_run.run_name,
            description=collection_params.description,
            embedder_config=collection_params.embedder_config,
        )
        return collection

    def get_collections(self, names: Optional[List[str]]) -> List[Collection]:
        ml_runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.entity_type = '{json.dumps(MLRunTypes.COLLECTION.value)}'",
        )
        collections = []
        for ml_run in ml_runs:
            if names is not None and ml_run.run_name not in names:
                continue
            collection_params = CollectionParams.from_mlfoundry_params(
                params=ml_run.get_params()
            )
            collection = Collection(
                name=ml_run.run_name,
                description=collection_params.description,
                embedder_config=collection_params.embedder_config,
            )
            collections.append(collection)

        return collections

    def create_data_source(self, data_source: CreateDataSource) -> DataSource:
        fqn = get_data_source_fqn(data_source)

        existing_data_source = self.get_data_source_from_fqn(fqn=fqn)
        if existing_data_source:
            raise HTTPException(400, f"Data source with fqn {fqn} already exists.")

        created_data_source = self.client.create_run(
            ml_repo=self.ml_repo_name,
            run_name=self.CONSTANT_DATA_SOURCE_RUN_NAME,
            tags=DataSourceTags(
                metadata=data_source.metadata,
            ).to_mlfoundry_tags(),
        )
        created_data_source.log_params(
            param_dict=DataSourceParams(
                type=data_source.type,
                uri=data_source.uri,
                fqn=fqn,
            ).to_mlfoundry_params()
        )
        created_data_source.end()
        return DataSource(
            type=data_source.type,
            uri=data_source.uri,
            fqn=fqn,
            metadata=data_source.metadata,
        )

    def get_data_source_from_fqn(self, fqn: str) -> DataSource | None:
        runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.entity_type = '{json.dumps(MLRunTypes.DATA_SOURCE.value)}' and params.fqn = '{json.dumps(fqn)}'",
        )
        for run in runs:
            run_params = DataSourceParams.from_mlfoundry_params(params=run.get_params())
            run_tags = DataSourceTags.from_mlfoundry_tags(params=run.get_tags())
            return DataSource(
                type=run_params.type,
                uri=run_params.uri,
                fqn=run_params.fqn,
                metadata=run_tags.metadata,
            )

        return None

    def get_data_sources(self) -> List[DataSource]:
        runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.entity_type = '{json.dumps(MLRunTypes.DATA_SOURCE.value)}'",
        )
        data_sources: List[DataSource] = []
        for run in runs:
            run_params = DataSourceParams.from_mlfoundry_params(params=run.get_params())
            run_tags = DataSourceTags.from_mlfoundry_tags(params=run.get_tags())
            data_sources.append(
                DataSource(
                    type=run_params.type,
                    uri=run_params.uri,
                    fqn=run_params.fqn,
                    metadata=run_tags.metadata,
                )
            )
        return data_sources

    def create_data_ingestion_run(
        self, data_ingestion_run: CreateDataIngestionRun
    ) -> DataIngestionRun:
        created_data_ingestion_run = self.client.create_run(
            ml_repo=self.ml_repo_name,
            run_name=data_ingestion_run.collection_name,
            tags=DataIngestionRunTags(
                collection_name=data_ingestion_run.collection_name,
                data_source_fqn=data_ingestion_run.data_source_fqn,
                status=DataIngestionRunStatus.INITIALIZED.value,
            ).to_mlfoundry_tags(),
        )
        created_data_ingestion_run.log_params(
            param_dict=DataIngestionRunParams(
                collection_name=data_ingestion_run.collection_name,
                data_source_fqn=data_ingestion_run.data_source_fqn,
                data_ingestion_mode=data_ingestion_run.data_ingestion_mode,
                parser_config=data_ingestion_run.parser_config,
                raise_error_on_failure=data_ingestion_run.raise_error_on_failure,
            ).to_mlfoundry_params()
        )
        created_data_ingestion_run.end()
        return DataIngestionRun(
            name=created_data_ingestion_run.run_name,
            collection_name=data_ingestion_run.collection_name,
            data_source_fqn=data_ingestion_run.data_source_fqn,
            data_ingestion_mode=data_ingestion_run.data_ingestion_mode,
            parser_config=data_ingestion_run.parser_config,
            raise_error_on_failure=data_ingestion_run.raise_error_on_failure,
            status=DataIngestionRunStatus.INITIALIZED,
        )

    def get_data_ingestion_run(
        self, data_ingestion_run_name: str, no_cache: bool = False
    ) -> DataIngestionRun | None:
        run = self._get_run_by_name(run_name=data_ingestion_run_name, no_cache=no_cache)
        if not run:
            return None
        run_params = DataIngestionRunParams.from_mlfoundry_params(
            params=run.get_params()
        )
        run_tags = DataIngestionRunTags.from_mlfoundry_tags(params=run.get_tags())
        data_ingestion_run = DataIngestionRun(
            name=run.run_name,
            collection_name=run_params.collection_name,
            data_source_fqn=run_params.data_source_fqn,
            data_ingestion_mode=DataIngestionMode(run_params.data_ingestion_mode),
            parser_config=run_params.parser_config,
            raise_error_on_failure=run_params.raise_error_on_failure,
            status=DataIngestionRunStatus(run_tags.status),
        )
        return data_ingestion_run

    def get_data_ingestion_runs(
        self, collection_name: str, data_source_fqn: str
    ) -> List[DataIngestionRun]:
        runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.entity_type = '{json.dumps(MLRunTypes.DATA_INGESTION_RUN.value)}' and params.collection_name = '{json.dumps(collection_name)}' and params.data_source_fqn = '{json.dumps(data_source_fqn)}'",
        )
        data_ingestion_runs: List[DataIngestionRun] = []
        for run in runs:
            run_params = DataIngestionRunParams.from_mlfoundry_params(
                params=run.get_params()
            )
            run_tags = DataIngestionRunTags.from_mlfoundry_tags(params=run.get_tags())
            data_ingestion_runs.append(
                DataIngestionRun(
                    name=run.run_name,
                    collection_name=run_params.collection_name,
                    data_source_fqn=run_params.data_source_fqn,
                    data_ingestion_mode=DataIngestionMode(
                        run_params.data_ingestion_mode
                    ),
                    parser_config=run_params.parser_config,
                    raise_error_on_failure=run_params.raise_error_on_failure,
                    status=DataIngestionRunStatus(run_tags.status),
                )
            )
        return data_ingestion_runs

    def delete_collection(self, collection_name: str, include_runs=False):
        collection = self._get_run_by_name(run_name=collection_name, no_cache=True)
        if not collection:
            return
        if include_runs:
            collection_inderer_job_runs = self.client.search_runs(
                ml_repo=self.ml_repo_name,
                filter_string=f"params.entity_type = '{json.dumps(MLRunTypes.DATA_INGESTION_RUN.value)}' and params.collection_name = '{json.dumps(collection_name)}'",
            )
            for collection_inderer_job_run in collection_inderer_job_runs:
                collection_inderer_job_run.delete()
        collection.delete()

    def update_data_ingestion_run_status(
        self,
        data_ingestion_run_name: str,
        status: DataIngestionRunStatus,
    ):
        data_ingestion_run = self._get_run_by_name(run_name=data_ingestion_run_name)
        if not data_ingestion_run:
            raise HTTPException(
                404, f"Data ingestion run {data_ingestion_run_name} not found."
            )
        data_ingestion_run.set_tags({"status": json.dumps(status.value)})

    def log_metrics_for_data_ingestion_run(
        self,
        data_ingestion_run_name: str,
        metric_dict: dict[str, int | float],
        step: int = 0,
    ):
        data_ingestion_run = self._get_run_by_name(run_name=data_ingestion_run_name)
        if not data_ingestion_run:
            raise HTTPException(
                404, f"Data ingestion run {data_ingestion_run_name} not found."
            )
        data_ingestion_run.log_metrics(metric_dict=metric_dict, step=step)
