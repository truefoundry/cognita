import enum
import json
import logging
import os
import tempfile
import warnings
from typing import Any, Dict, List

import mlflow
import mlfoundry
from fastapi import HTTPException

from backend.modules.metadata_store.base import BaseMetadataStore, get_data_source_fqn
from backend.types import (
    AssociateDataSourceWithCollection,
    AssociatedDataSources,
    Collection,
    CreateCollection,
    CreateDataIngestionRun,
    CreateDataSource,
    DataIngestionRun,
    DataIngestionRunStatus,
    DataSource,
)


class MLRunTypes(str, enum.Enum):
    """
    Configuration defining types of ML Runs allowed
    """
    COLLECTION = "COLLECTION"
    DATA_INGESTION_RUN = "DATA_INGESTION_RUN"
    DATA_SOURCE = "DATA_SOURCE"

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
        """
        Create a collection from given CreateCollection object. 
        It primarly has collection name, collection description and embedder congfiguration
        """
        existing_collection = self.get_collection_by_name(
            collection_name=collection.name, no_cache=True
        )
        if existing_collection:
            raise HTTPException(
                status_code=400,
                detail=f"Collection with name {collection.name} already exists.",
            )
        params = {
            "entity_type": MLRunTypes.COLLECTION.value,
            "collection_name": collection.name,
        }

        run = self.client.create_run(
            ml_repo=self.ml_repo_name,
            run_name=collection.name,
            tags=params,
        )
        created_collection = Collection(
            name=collection.name,
            description=collection.description,
            embedder_config=collection.embedder_config,
        )
        self._save_entity_to_run(
            run=run, metadata=created_collection.dict(), params=params
        )
        run.end()
        return created_collection

    def _get_entity_from_run(
        self,
        run: mlfoundry.MlFoundryRun,
    ) -> Dict[str, Any]:
        artifact = self._get_artifact_metadata_ml_run(run)
        metadata = artifact.metadata
        if not metadata:
            raise HTTPException(
                404,
                f"Entity {run.run_name} was manupulated: metadata artifact not found.",
            )
        return metadata

    def _get_artifact_metadata_ml_run(
        self, run: mlfoundry.MlFoundryRun
    ) -> mlfoundry.ArtifactVersion | None:
        params = run.get_params()
        metadata_artifact_fqn = params.get("metadata_artifact_fqn")
        if not metadata_artifact_fqn:
            raise HTTPException(
                404,
                f"Entity {run.run_name} was manupulated: metadata_artifact_fqn not found.",
            )
        artifacts = run.list_artifact_versions()
        for artifact in artifacts:
            if artifact.fqn == metadata_artifact_fqn:
                return artifact
        return None

    def _save_entity_to_run(
        self,
        run: mlfoundry.MlFoundryRun,
        metadata: Dict[str, Any],
        params: Dict[str, str],
    ):
        with tempfile.TemporaryDirectory() as tmpdirname:
            file_path = os.path.join(tmpdirname, "metadata.json")
            with open(file_path, "w") as f:
                f.write(json.dumps(metadata))
            artifact = run.log_artifact(
                name=run.run_name,
                artifact_paths=[mlfoundry.ArtifactPath(src=file_path)],
                description="This artifact contains the entity",
                metadata=metadata,
            )
            run.log_params({"metadata_artifact_fqn": artifact.fqn, **params})

    def _update_entity_in_run(
        self,
        run: mlfoundry.MlFoundryRun,
        metadata: Dict[str, Any],
    ):
        artifact = self._get_artifact_metadata_ml_run(run)
        artifact.metadata = metadata
        artifact.update()

    def get_collection_by_name(
        self, collection_name: str, no_cache: bool = True
    ) -> Collection | None:
        """Get collection from given collection name."""
        ml_run = self._get_run_by_name(run_name=collection_name, no_cache=no_cache)
        if not ml_run:
            return None
        return self._polulate_collection(
            Collection.parse_obj(self._get_entity_from_run(run=ml_run))
        )

    def get_collections(self) -> List[Collection]:
        """Get all the collections for the given client"""
        ml_runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.entity_type = '{MLRunTypes.COLLECTION.value}'",
        )
        collections = []
        for ml_run in ml_runs:
            collection = Collection.parse_obj(self._get_entity_from_run(run=ml_run))
            collections.append(self._polulate_collection(collection))
        return collections

    def _polulate_collection(self, collection: Collection):
        for (
            data_source_fqn,
            associated_data_source,
        ) in collection.associated_data_sources.items():
            data_source = self.get_data_source_from_fqn(data_source_fqn)
            associated_data_source.data_source = data_source
            collection.associated_data_sources[data_source_fqn] = associated_data_source
        return collection

    def associate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_association: AssociateDataSourceWithCollection,
    ) -> Collection:
        collection_run = self._get_run_by_name(
            run_name=collection_name,
            no_cache=True,
        )
        if not collection_run:
            raise HTTPException(
                404,
                f"Collection {collection_name} not found.",
            )
        # Always do this to avoid race conditions
        collection = Collection.parse_obj(self._get_entity_from_run(run=collection_run))
        associated_data_source = AssociatedDataSources(
            data_source_fqn=data_source_association.data_source_fqn,
            parser_config=data_source_association.parser_config,
        )
        collection.associated_data_sources[data_source_association.data_source_fqn] = (
            associated_data_source
        )

        self._update_entity_in_run(run=collection_run, metadata=collection.dict())
        return self._polulate_collection(collection)

    def unassociate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_fqn: str,
    ) -> Collection:
        collection_run = self._get_run_by_name(
            run_name=collection_name,
            no_cache=True,
        )
        if not collection_run:
            raise HTTPException(
                404,
                f"Collection {collection_name} not found.",
            )
        # Always do this to avoid run conditions
        collection = Collection.parse_obj(self._get_entity_from_run(run=collection_run))
        collection.associated_data_sources.pop(data_source_fqn)
        self._update_entity_in_run(run=collection_run, metadata=collection.dict())
        return collection

    def create_data_source(self, data_source: CreateDataSource) -> DataSource:
        fqn = get_data_source_fqn(data_source)

        existing_data_source = self.get_data_source_from_fqn(fqn=fqn)
        if existing_data_source:
            raise HTTPException(400, f"Data source with fqn {fqn} already exists.")

        params = {
            "entity_type": MLRunTypes.DATA_SOURCE.value,
            "data_source_fqn": fqn,
        }
        run = self.client.create_run(
            ml_repo=self.ml_repo_name,
            run_name=self.CONSTANT_DATA_SOURCE_RUN_NAME,
            tags=params,
        )
        created_data_source = DataSource(
            type=data_source.type,
            uri=data_source.uri,
            fqn=fqn,
            metadata=data_source.metadata,
        )
        self._save_entity_to_run(
            run=run, metadata=created_data_source.dict(), params=params
        )
        run.end()
        return created_data_source

    def get_data_source_from_fqn(self, fqn: str) -> DataSource | None:
        runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.entity_type = '{MLRunTypes.DATA_SOURCE.value}' and params.data_source_fqn = '{fqn}'",
        )
        for run in runs:
            data_source = DataSource.parse_obj(self._get_entity_from_run(run=run))
            return data_source

        return None

    def get_data_sources(self) -> List[DataSource]:
        runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.entity_type = '{MLRunTypes.DATA_SOURCE.value}'",
        )
        data_sources: List[DataSource] = []
        for run in runs:
            data_source = DataSource.parse_obj(self._get_entity_from_run(run=run))
            data_sources.append(data_source)
        return data_sources

    def create_data_ingestion_run(
        self, data_ingestion_run: CreateDataIngestionRun
    ) -> DataIngestionRun:
        params = {
            "entity_type": MLRunTypes.DATA_INGESTION_RUN.value,
            "collection_name": data_ingestion_run.collection_name,
            "data_source_fqn": data_ingestion_run.data_source_fqn,
        }
        run = self.client.create_run(
            ml_repo=self.ml_repo_name,
            run_name=data_ingestion_run.collection_name,
            tags={
                **params,
                "status": DataIngestionRunStatus.INITIALIZED.value,
            },
        )
        created_data_ingestion_run = DataIngestionRun(
            name=run.run_name,
            collection_name=data_ingestion_run.collection_name,
            data_source_fqn=data_ingestion_run.data_source_fqn,
            data_ingestion_mode=data_ingestion_run.data_ingestion_mode,
            parser_config=data_ingestion_run.parser_config,
            raise_error_on_failure=data_ingestion_run.raise_error_on_failure,
            status=DataIngestionRunStatus.INITIALIZED,
        )
        self._save_entity_to_run(
            run=run, metadata=created_data_ingestion_run.dict(), params=params
        )
        run.end()
        return created_data_ingestion_run

    def get_data_ingestion_run(
        self, data_ingestion_run_name: str, no_cache: bool = False
    ) -> DataIngestionRun | None:
        run = self._get_run_by_name(run_name=data_ingestion_run_name, no_cache=no_cache)
        if not run:
            return None
        data_ingestion_run = DataIngestionRun.parse_obj(
            self._get_entity_from_run(run=run)
        )
        run_tags = run.get_tags()
        data_ingestion_run.status = DataIngestionRunStatus(run_tags.get("status"))
        return data_ingestion_run

    def get_data_ingestion_runs(
        self, collection_name: str, data_source_fqn: str
    ) -> List[DataIngestionRun]:
        runs = self.client.search_runs(
            ml_repo=self.ml_repo_name,
            filter_string=f"params.entity_type = '{MLRunTypes.DATA_INGESTION_RUN.value}' and params.collection_name = '{collection_name}' and params.data_source_fqn = '{data_source_fqn}'",
        )
        data_ingestion_runs: List[DataIngestionRun] = []
        for run in runs:
            data_ingestion_run = DataIngestionRun.parse_obj(
                self._get_entity_from_run(run=run)
            )
            run_tags = run.get_tags()
            data_ingestion_run.status = DataIngestionRunStatus(run_tags.get("status"))
            data_ingestion_runs.append(data_ingestion_run)
        return data_ingestion_runs

    def delete_collection(self, collection_name: str, include_runs=False):
        collection = self._get_run_by_name(run_name=collection_name, no_cache=True)
        if not collection:
            return
        if include_runs:
            collection_inderer_job_runs = self.client.search_runs(
                ml_repo=self.ml_repo_name,
                filter_string=f"params.entity_type = '{MLRunTypes.DATA_INGESTION_RUN.value}' and params.collection_name = '{collection_name}'",
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

    def log_errors_for_data_ingestion_run(
        self, data_ingestion_run_name: str, errors: Dict[str, Any]
    ):
        data_ingestion_run = self._get_run_by_name(run_name=data_ingestion_run_name)
        if not data_ingestion_run:
            raise HTTPException(
                404, f"Data ingestion run {data_ingestion_run_name} not found."
            )
        with tempfile.TemporaryDirectory() as tmpdirname:
            file_path = os.path.join(tmpdirname, "error.json")
            with open(file_path, "w") as f:
                f.write(json.dumps(errors))
            data_ingestion_run.log_artifact(
                name=data_ingestion_run.run_name,
                artifact_paths=[mlfoundry.ArtifactPath(src=file_path)],
                description="This artifact contains the errors during run",
            )
