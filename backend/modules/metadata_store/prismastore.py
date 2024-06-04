import asyncio
import enum
import json
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException
from prisma import Prisma

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


class PrismaStore(BaseMetadataStore):
    def __init__(self, db) -> None:
        self.db = db

    @classmethod
    async def connect(cls):
        try:
            db = Prisma()
            await db.connect()
            logger.info(f"Connected to Prisma....")
            return cls(db)
        except Exception as e:
            logger.error(f"Failed to connect to Prisma: {e}")
            raise HTTPException(status_code=500, detail="Failed to connect to Prisma")

    async def create_collection(self, collection: CreateCollection) -> Collection:
        try:
            existing_collection = await self.get_collection_by_name(collection.name)
            if existing_collection:
                logger.error(f"Collection with name {collection.name} already exists")
                raise HTTPException(
                    status_code=400,
                    detail=f"Collection with name {collection.name} already exists",
                )
        except Exception as e:
            logger.error(f"Failed to check if collection exists: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to check if collection exists"
            )

        try:
            collection = await self.db.collection.create(data=collection.dict())
            return Collection(**collection)
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise HTTPException(status_code=500, detail="Failed to create collection")

    async def get_collection_by_name(
        self, collection_name: str, no_cache: bool = True
    ) -> Collection | None:
        try:
            collection = await self.db.collection.find_first(
                where={"name": collection_name}
            )
            if collection:
                return Collection(**collection)
            return None
        except Exception as e:
            logger.error(f"Failed to get collection by name: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to get collection by name"
            )

    async def get_collections(self) -> List[Collection]:
        try:
            collections = await self.db.collection.find_many()
            return [Collection(**collection) for collection in collections]
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            raise HTTPException(status_code=500, detail="Failed to get collections")

    async def list_collections(self) -> List[str]:
        try:
            collections = await self.get_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise HTTPException(status_code=500, detail="Failed to list collections")

    async def delete_collection(self, collection_name: str, include_runs=False):
        try:
            collection = await self.get_collection_by_name(collection_name)
            if not collection:
                logger.error(f"Collection with name {collection_name} does not exist")
                raise HTTPException(
                    status_code=400,
                    detail=f"Collection with name {collection_name} does not exist",
                )
        except Exception as e:
            logger.error(f"Failed to check if collection exists: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to check if collection exists"
            )

        try:
            await self.db.collection.delete(where={"name": collection_name})
            if include_runs:
                await self.db.dataIngestionRun.delete(
                    where={"collectionName": collection_name}
                )
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete collection")

    async def create_data_source(self, data_source: CreateDataSource) -> DataSource:
        try:
            existing_data_source = await self.get_data_source_from_fqn(data_source.fqn)
            if existing_data_source:
                logger.error(f"Data source with fqn {data_source.fqn} already exists")
                raise HTTPException(
                    status_code=400,
                    detail=f"Data source with fqn {data_source.fqn} already exists",
                )
        except Exception as e:
            logger.error(f"Failed to check if data source exists: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to check if data source exists"
            )

        try:
            data = data_source.dict()
            # convert metadata to json string
            data["metadata"] = json.dumps(data["metadata"])

            logger.info(f"Creating data source: {data}")
            data_source = await self.db.datasource.create(data)
            logger.info(f"Created data source: {data_source}")
            return data_source
        except Exception as e:
            logger.error(f"Failed to create data source: {e}")
            raise HTTPException(status_code=500, detail="Failed to create data source")

    async def get_data_source_from_fqn(self, fqn: str) -> DataSource | None:
        try:
            data_source = await self.db.datasource.find_first(where={"fqn": fqn})
            if data_source:
                return data_source
            return None
        except Exception as e:
            logger.error(f"Failed to get data source by fqn: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to get data source by fqn"
            )

    async def get_data_sources(self) -> List[DataSource]:
        try:
            data_sources = await self.db.datasource.find_many()
            # return [DataSource(**data_source) for data_source in data_sources]
            return data_sources
        except Exception as e:
            logger.error(f"Failed to get data sources: {e}")
            raise HTTPException(status_code=500, detail="Failed to get data sources")

    async def associate_data_source_with_collection(
        self, association: AssociateDataSourceWithCollection
    ) -> Collection:
        try:
            collection = await self.get_collection_by_name(association.collection_name)
            if not collection:
                logger.error(
                    f"Collection with name {association.collection_name} does not exist"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Collection with name {association.collection_name} does not exist",
                )
        except Exception as e:
            logger.error(f"Failed to check if collection exists: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to check if collection exists"
            )

        try:
            data_source = await self.get_data_source_from_fqn(
                association.data_source_fqn
            )
            if not data_source:
                logger.error(
                    f"Data source with fqn {association.data_source_fqn} does not exist"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Data source with fqn {association.data_source_fqn} does not exist",
                )
        except Exception as e:
            logger.error(f"Failed to check if data source exists: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to check if data source exists"
            )

        try:
            await self.db.associatedDataSources.create(data=association.dict())
            return collection
        except Exception as e:
            logger.error(f"Failed to associate data source with collection: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to associate data source with collection",
            )

    async def unassociate_data_source_with_collection(
        self, collection_name: str, data_source_fqn: str
    ) -> Collection:
        try:
            collection = await self.get_collection_by_name(collection_name)
            if not collection:
                logger.error(f"Collection with name {collection_name} does not exist")
                raise HTTPException(
                    status_code=400,
                    detail=f"Collection with name {collection_name} does not exist",
                )
        except Exception as e:
            logger.error(f"Failed to check if collection exists: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to check if collection exists"
            )

        try:
            data_source = await self.get_data_source_from_fqn(data_source_fqn)
            if not data_source:
                logger.error(f"Data source with fqn {data_source_fqn} does not exist")
                raise HTTPException(
                    status_code=400,
                    detail=f"Data source with fqn {data_source_fqn} does not exist",
                )
        except Exception as e:
            logger.error(f"Failed to check if data source exists: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to check if data source exists"
            )

        try:
            await self.db.associatedDataSources.delete(
                where={
                    "collectionName": collection_name,
                    "dataSourceFqn": data_source_fqn,
                }
            )
            return collection
        except Exception as e:
            logger.error(f"Failed to unassociate data source with collection: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to unassociate data source with collection",
            )

    async def list_data_sources(
        self,
    ) -> List[dict[str, str]]:
        try:
            data_sources = await self.get_data_sources()
            logger.info(f"Data sources: {data_sources}")
            return [data_source.dict() for data_source in data_sources]
        except Exception as e:
            logger.error(f"Failed to list data sources: {e}")
            raise HTTPException(status_code=500, detail="Failed to list data sources")

    async def create_data_ingestion_run(
        self, data_ingestion_run: CreateDataIngestionRun
    ) -> DataIngestionRun:
        try:
            existing_data_ingestion_run = await self.get_data_ingestion_run(
                data_ingestion_run.name
            )
            if existing_data_ingestion_run:
                logger.error(
                    f"Data ingestion run with name {data_ingestion_run.name} already exists"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Data ingestion run with name {data_ingestion_run.name} already exists",
                )
        except Exception as e:
            logger.error(f"Failed to check if data ingestion run exists: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to check if data ingestion run exists"
            )

        try:
            data_ingestion_run = await self.db.dataIngestionRun.create(
                data=data_ingestion_run.dict()
            )
            return DataIngestionRun(**data_ingestion_run)
        except Exception as e:
            logger.error(f"Failed to create data ingestion run: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to create data ingestion run"
            )

    async def get_data_ingestion_run(
        self, data_ingestion_run_name: str, no_cache: bool = False
    ) -> DataIngestionRun | None:
        try:
            data_ingestion_run = await self.db.dataIngestionRun.find_first(
                where={"name": data_ingestion_run_name}
            )
            if data_ingestion_run:
                return DataIngestionRun(**data_ingestion_run)
            return None
        except Exception as e:
            logger.error(f"Failed to get data ingestion run by name: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to get data ingestion run by name"
            )

    async def get_data_ingestion_runs(
        self, collection_name: str, data_source_fqn: str = None
    ) -> List[DataIngestionRun]:
        try:
            data_ingestion_runs = await self.db.dataIngestionRun.find_many(
                where={"collectionName": collection_name}
            )
            return [
                DataIngestionRun(**data_ingestion_run)
                for data_ingestion_run in data_ingestion_runs
            ]
        except Exception as e:
            logger.error(f"Failed to get data ingestion runs: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to get data ingestion runs"
            )

    async def update_data_ingestion_run_status(
        self, data_ingestion_run_name: str, status: DataIngestionRunStatus
    ) -> DataIngestionRun:
        try:
            data_ingestion_run = await self.get_data_ingestion_run(
                data_ingestion_run_name
            )
            if not data_ingestion_run:
                logger.error(
                    f"Data ingestion run with name {data_ingestion_run_name} does not exist"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Data ingestion run with name {data_ingestion_run_name} does not exist",
                )
        except Exception as e:
            logger.error(f"Failed to check if data ingestion run exists: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to check if data ingestion run exists"
            )

        try:
            await self.db.dataIngestionRun.update(
                where={"name": data_ingestion_run_name}, data={"status": status}
            )
            return await self.get_data_ingestion_run(data_ingestion_run_name)
        except Exception as e:
            logger.error(f"Failed to update data ingestion run status: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to update data ingestion run status"
            )

    async def log_metrics_for_data_ingestion_run(
        self,
        data_ingestion_run_name: str,
        metric_dict: dict[str, int | float],
        step: int = 0,
    ):
        pass

    async def log_errors_for_data_ingestion_run(
        self, data_ingestion_run_name: str, errors: Dict[str, Any]
    ):
        pass


if __name__ == "__main__":
    # initialize the PrismaStore
    prisma_store = PrismaStore.connect()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(prisma_store)
