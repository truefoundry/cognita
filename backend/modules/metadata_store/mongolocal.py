import json
import os
import tempfile
import warnings
from typing import Any, Dict, List

from fastapi import HTTPException
from pymongo.mongo_client import MongoClient

from backend.logger import logger
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


class MongoMetadataStore(BaseMetadataStore):
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.client = MongoClient(config["uri"])
        try:
            self.client.admin.command("ping")
            logger.info(
                "Pinged your deployment. You successfully connected to MongoDB!"
            )
        except Exception as e:
            logger.error(e)

        # Create a new database if it does not exist by name of `tf` if it does not exist
        # MongoDB waits until you have created a collection (table), with at least one document (record) before it actually creates the database (and collection).
        self.db = self.client["tf"]
        # Create a new collection if it does not exist by name of `collections` if it does not exist
        self.collections = self.db["collections"]
        # Create a new collection if it does not exist by name of `data_sources` if it does not exist
        self.data_sources = self.db["data_sources"]

    def create_collection(self, collection: CreateCollection) -> Collection:
        """
        Create a collection (record) in the collections (table)
        """

        # Check if collection already exists
        existing_collection = self.get_collection_by_name(collection.name)
        if existing_collection:
            logger.error(f"Collection with name {collection.name} already exists")
            raise HTTPException(
                status_code=400,
                detail=f"Collection with name {collection.name} already exists",
            )

        # Insert the collection into the `collections` table in `tf` database in MongoDB, check if success and return the collection
        collection_dict = collection.dict()
        try:
            result = self.collections.insert_one(collection_dict)
            if result.acknowledged:
                return collection
            logger.error(f"Failed to create collection {collection.name}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create collection {collection.name}",
            )
        except Exception as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create collection {collection.name}",
            )

    def get_collection_by_name(
        self, collection_name: str, no_cache: bool = True
    ) -> Collection | None:
        """
        Get a collection (record) from the collections (table) by name
        """
        # Check if collection exists in `collections` table in `tf` database in MongoDB
        # If it does, return the collection else None.
        collection = self.collections.find_one({"name": collection_name})
        if collection:
            return Collection(**collection)
        return None

    def get_collections(
        self,
    ) -> List[Collection]:
        """
        Get all collections from collections (table)
        """
        # return all collections, if any, from `collections` table in `tf` database in MongoDB
        collections = self.collections.find()
        return [Collection(**collection) for collection in collections]

    def create_data_source(self, data_source: CreateDataSource) -> DataSource:
        """
        Create a data source in the data_sources (table)
        """
        # Add data source to `data_sources` table in `tf` database in MongoDB
        data_source_dict = data_source.dict()
        # Add fully qualified name (fqn) to the data source -> Property type
        data_source_dict["fqn"] = data_source.fqn
        try:
            result = self.data_sources.insert_one(data_source_dict)
            if result.acknowledged:
                return data_source
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create data source {data_source.name}",
            )
        except Exception as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create data source {data_source.name}",
            )

    def get_data_source_from_fqn(self, fqn: str) -> DataSource | None:
        """
        Get a data source from the data_sources (table) by fqn
        """
        # Check if data source exists in `data_sources` table in `tf` database in MongoDB
        # If it does, return the data source else None.
        data_source = self.data_sources.find_one({"fqn": fqn})
        if data_source:
            return DataSource(**data_source)
        return None

    def get_data_sources(self) -> List[DataSource]:
        """
        Get all data sources from the data_sources (table)
        """
        # return all data sources, if any, from `data_sources` table in `tf` database in MongoDB
        data_sources = self.data_sources.find()
        return [DataSource(**data_source) for data_source in data_sources]

    def create_data_ingestion_run(
        self, data_ingestion_run: CreateDataIngestionRun
    ) -> DataIngestionRun:
        """
        Create a data ingestion run in the metadata store
        """
        pass

    def get_data_ingestion_run(
        self, data_ingestion_run_name: str, no_cache: bool = False
    ) -> DataIngestionRun | None:
        """
        Get a data ingestion run from the metadata store by name
        """
        pass

    def get_data_ingestion_runs(
        self, collection_name: str, data_source_fqn: str = None
    ) -> List[DataIngestionRun]:
        """
        Get all data ingestion runs from the metadata store
        """
        pass

    def delete_collection(self, collection_name: str, include_runs=False):
        """
        Delete a collection given it's name from the collections (table)
        """
        # Check if collection exists in `collections` table in `tf` database in MongoDB
        # If it does, delete the collection else raise an error.
        collection = self.get_collection_by_name(collection_name)
        if collection:
            result = self.collections.delete_one({"name": collection_name})
            if not result.acknowledged:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete collection {collection_name}",
                )

            # TODO: Delete assoicated data ingestion runs too.
        logger.debug(f"[Metadata Store] Deleted colelction {collection_name}")
        return

    def associate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_association: AssociateDataSourceWithCollection,
    ) -> Collection:
        """
        Associate a data source with a collection (record) in the collections table
        """
        # Check if collection exists in `collections` table in `tf` database in MongoDB
        # If it does, associate the data source with the collection else raise an error.
        collection = self.get_collection_by_name(collection_name)
        if collection:
            # check if data source exists
            data_source = self.get_data_source_from_fqn(
                data_source_association.data_source_fqn
            )
            if data_source:
                associated_data_src = AssociatedDataSources(
                    data_source_fqn=data_source_association.data_source_fqn,
                    parser_config=data_source_association.parser_config,
                    data_source=data_source.dict(),
                )
                # Add an associated_data_sources dict, where each key is associated_data_src.data_source_fqn and value is associated_data_src
                collection.associated_data_sources[
                    data_source_association.data_source_fqn
                ] = associated_data_src
                try:
                    # append the data source fqn to the collection's data_sources list
                    result = self.collections.update_one(
                        {"name": collection_name},
                        {
                            "$set": {
                                f"associated_data_sources.{data_source_association.data_source_fqn}": associated_data_src.dict()
                            }
                        },
                    )
                    if not result.acknowledged:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to associate data source {data_source_association.data_source_fqn} with collection {collection_name}",
                        )
                    return collection
                except Exception as e:
                    logger.error(e)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to associate data source {data_source_association.data_source_fqn} with collection {collection_name}",
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Data source {data_source_association.data_source_fqn} not found",
                )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Collection {collection_name} not found",
            )

    def unassociate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_fqn: str,
    ) -> Collection:
        """
        Unassociate a data source with a collection in the collections (table)
        """
        # Check if collection exists in `collections` table in `tf` database in MongoDB
        # If it does, unassociate the data source with the collection else raise an error.
        collection = self.get_collection_by_name(collection_name)
        if collection:
            if data_source_fqn in collection["data_sources"]:
                collection["data_sources"].remove(data_source_fqn)
                try:
                    result = self.collections.update_one(
                        {"name": collection_name},
                        {"$set": {"data_sources": collection["data_sources"]}},
                    )
                    if not result.acknowledged:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to unassociate data source {data_source_fqn} with collection {collection_name}",
                        )
                    return Collection(**collection)
                except Exception as e:
                    logger.error(e)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to unassociate data source {data_source_fqn} with collection {collection_name}",
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Data source {data_source_fqn} not associated with collection {collection_name}",
                )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Collection {collection_name} not found",
            )

    def update_data_ingestion_run_status(
        self,
        data_ingestion_run_name: str,
        status: DataIngestionRunStatus,
    ):
        """
        Update the status of a data ingestion run in the metadata store
        """
        pass

    def log_metrics_for_data_ingestion_run(
        self,
        data_ingestion_run_name: str,
        metric_dict: dict[str, int | float],
        step: int = 0,
    ):
        """
        Log metrics for a data ingestion run in the metadata store
        """
        pass

    def log_errors_for_data_ingestion_run(
        self, data_ingestion_run_name: str, errors: Dict[str, Any]
    ):
        """
        Log errors for a data ingestion run in the metadata store
        """
        pass

    async def list_collections(
        self,
    ) -> List[str]:
        """
        List all collection names from collections (table)
        """
        # return all collection names, if any, from `collections` table in `tf` database in MongoDB
        collections = self.collections.find()
        return [collection["name"] for collection in collections]

    async def list_data_sources(
        self,
    ) -> List[dict[str, str]]:
        """
        List all data source names from collections (table), return dict of type, uri and fqn
        """
        # return all data source names, if any, from `data_sources` table in `tf` database in MongoDB
        data_sources = self.data_sources.find()
        return [
            {
                "type": data_source["type"],
                "uri": data_source["uri"],
                "fqn": data_source["fqn"],
            }
            for data_source in data_sources
        ]


if __name__ == "__main__":
    config = {
        "uri": "mongodb+srv://prathamesh:ebFn8dtC8z2SGIWE@tf-mongo-cluster.3ogijay.mongodb.net/"
    }
    metadata_store = MongoMetadataStore(config)
