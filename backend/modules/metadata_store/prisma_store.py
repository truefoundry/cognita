import asyncio
import json
import os
import random
import shutil
import string
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from fastapi import HTTPException
from prisma import Prisma
from prisma.errors import RecordNotFoundError, UniqueViolationError

from backend.logger import logger
from backend.modules.metadata_store.base import BaseMetadataStore
from backend.settings import settings
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
    RagApplication,
)
from backend.utils import TRUEFOUNDRY_CLIENT

if TYPE_CHECKING:
    # TODO (chiragjn): Can we import these safely even if the prisma client might not be generated yet?
    from prisma.models import Collection as PrismaCollection
    from prisma.models import DataSource as PrismaDataSource
    from prisma.models import IngestionRuns as PrismaDataIngestionRun
    from prisma.models import RagApps as PrismaRagApplication

# TODO (chiragjn):
#   - Use transactions!
#   - Some methods are using json.dumps - not sure if this is the right way to send data via prisma client
#   - primsa generates its own DB entity classes - ideally we should be using those instead of call
#       .model_dump() on the pydantic objects. See prisma.models and prisma.actions
#


class PrismaStore(BaseMetadataStore):
    def __init__(self, *args, db: Prisma, **kwargs) -> None:
        self.db = db
        super().__init__(*args, **kwargs)

    @classmethod
    async def aconnect(cls, **kwargs):
        # Create a new Prisma client instance
        db = Prisma()
        # Connect to the database
        await db.connect()
        # Log the connection
        logger.info(f"Connected to Prisma")
        # Return a new instance of the class with the database connection
        return cls(db=db, **kwargs)

    ######
    # COLLECTIONS APIS
    ######

    async def aget_collection_by_name(
        self, collection_name: str, no_cache: bool = True
    ) -> Optional[Collection]:
        # Fetch the collection by name
        collection: "PrismaCollection" = await self.db.collection.find_first_or_raise(
            where={"name": collection_name}
        )
        # Validate the collection and return it
        return Collection.model_validate(collection.model_dump())

    async def acreate_collection(self, collection: CreateCollection) -> Collection:
        logger.info(f"Creating collection: {collection.model_dump()}")
        collection_data = collection.model_dump()
        collection_data["embedder_config"] = json.dumps(
            collection_data["embedder_config"]
        )
        collection: "PrismaCollection" = await self.db.collection.create(
            data=collection_data
        )
        return Collection.model_validate(collection.model_dump())

    async def aget_collections(self) -> List[Collection]:
        collections: List["PrismaCollection"] = await self.db.collection.find_many(
            order={"id": "desc"},
        )
        return [Collection.model_validate(c.model_dump()) for c in collections]

    async def alist_collections(self) -> List[str]:
        collections = await self.aget_collections()
        return [collection.name for collection in collections]

    # TODO: (mnvsk97) Add association between collections and ingestion runs and delete all associated records using `includes`. See: https://prisma-client-py.readthedocs.io/en/stable/reference/operations/#unique-record
    async def adelete_collection(self, collection_name: str, include_runs=False):
        # Initialize a database transaction
        async with self.db.tx() as transaction:
            # Delete ingestion runs first if include_runs is True
            if include_runs:
                deleted_runs = await transaction.ingestionruns.delete_many(
                    where={"collection_name": collection_name}
                )
                logger.info(f"Deleted ingestion runs for collection {collection_name}")

            # Delete the collection
            deleted_collection = await transaction.collection.delete(
                where={"name": collection_name}
            )
            if not deleted_collection:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to delete collection {collection_name!r}. No such record found",
                )

            logger.info(f"Successfully deleted collection: {deleted_collection.name}")
            return deleted_collection

    ######
    # DATA SOURCE APIS
    ######
    async def aget_data_source_from_fqn(self, fqn: str) -> DataSource:
        # Fetch the data source from the database by fqn. If not found, raise a RecordNotFoundError
        data_source: "PrismaDataSource" = await self.db.datasource.find_first_or_raise(
            where={"fqn": fqn}
        )
        # Validate the data source and return it
        return DataSource.model_validate(data_source.model_dump())

    async def acreate_data_source(self, data_source: CreateDataSource) -> DataSource:
        # If metadata is not provided, remove it from the payload
        data_source_dict = data_source.model_dump(exclude_unset=True)

        if data_source_dict.get("metadata") is None:
            data_source_dict.pop("metadata", None)

        # If metadata is provided, convert it to a JSON string
        if isinstance(data_source_dict.get("metadata"), dict):
            data_source_dict["metadata"] = json.dumps(data_source_dict["metadata"])

        # Create the data source
        data_source: "PrismaDataSource" = await self.db.datasource.create(
            data=data_source_dict
        )
        logger.info(f"Created data source: {data_source}")
        # Validate the data source and return it
        return DataSource.model_validate(data_source.model_dump())

    async def aget_data_sources(self) -> List[DataSource]:
        data_sources: List["PrismaDataSource"] = await self.db.datasource.find_many(
            order={"id": "desc"}
        )
        return [
            DataSource.model_validate(data_source.model_dump())
            for data_source in data_sources
        ]

    async def aassociate_data_sources_with_collection(
        self,
        collection_name: str,
        data_source_associations: List[AssociateDataSourceWithCollection],
    ) -> Collection:
        # Get the collection by name
        collection = await self.aget_collection_by_name(collection_name)

        # Get the existing associated data sources. If not found, initialize an empty dict.
        existing_associated_data_sources = collection.associated_data_sources

        # Fetch all data sources in a single query
        data_source_fqns = [assoc.data_source_fqn for assoc in data_source_associations]
        data_sources = await self.db.datasource.find_many(
            where={"fqn": {"in": data_source_fqns}}
        )
        data_sources_dict = {ds.fqn: ds for ds in data_sources}

        # Create AssociatedDataSources objects and update the existing_associated_data_sources
        for assoc in data_source_associations:
            data_source = data_sources_dict.get(assoc.data_source_fqn)
            if not data_source:
                raise HTTPException(
                    status_code=404,
                    detail=f"Data source with fqn {assoc.data_source_fqn} not found",
                )

            data_src_to_associate = AssociatedDataSources(
                data_source_fqn=assoc.data_source_fqn,
                parser_config=assoc.parser_config,
                data_source=DataSource.model_validate(data_source.model_dump()),
            )
            existing_associated_data_sources[
                assoc.data_source_fqn
            ] = data_src_to_associate

        # Convert the existing associated data sources to a dictionary
        associated_data_sources = {
            fqn: data_source.model_dump()
            for fqn, data_source in existing_associated_data_sources.items()
        }

        # Update the collection with the new associated data sources
        updated_collection = await self.db.collection.update(
            where={"name": collection_name},
            data={"associated_data_sources": json.dumps(associated_data_sources)},
        )

        # If the update fails, raise an HTTPException
        if not updated_collection:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to associate data sources with collection {collection_name!r}. No such record found",
            )

        # Validate the updated collection and return it
        return Collection.model_validate(updated_collection.model_dump())

    async def aunassociate_data_source_with_collection(
        self, collection_name: str, data_source_fqn: str
    ) -> Collection:
        # Get the collection by name
        collection = await self.aget_collection_by_name(collection_name)
        # Get the existing associated data sources
        associated_data_sources = collection.associated_data_sources or {}
        # If the data source is not associated with the collection, deletion is not possible and an error is raised
        if data_source_fqn not in associated_data_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Data source with fqn {data_source_fqn!r} not associated with collection {collection_name!r}",
            )
        # Remove the data source from associated data sources
        associated_data_sources.pop(data_source_fqn)

        # Convert the associated data sources to a dictionary
        updated_associated_data_sources = {
            fqn: ds.model_dump() for fqn, ds in associated_data_sources.items()
        }

        # Update the collection with the new associated data sources
        updated_collection = await self.db.collection.update(
            where={"name": collection_name},
            data={
                "associated_data_sources": json.dumps(updated_associated_data_sources)
            },
        )

        # If the update fails, raise an HTTPException
        if not updated_collection:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to unassociate data source from collection {collection_name!r}. No such record found",
            )

        # Validate the updated collection and return it
        return Collection.model_validate(updated_collection.model_dump())

    async def alist_data_sources(
        self,
    ) -> List[Dict[str, str]]:
        data_sources = await self.aget_data_sources()
        return [data_source.model_dump() for data_source in data_sources]

    async def adelete_data_source(self, data_source_fqn: str) -> None:
        # Fetch all collections
        collections = await self.aget_collections()
        # Check if data source is associated with any collection
        for collection in collections:
            associated_data_sources = collection.associated_data_sources or {}
            # If data source is associated with any collection, raise an error prompting the user to either delete the collection or unassociate the data source from the collection
            if data_source_fqn in associated_data_sources:
                logger.error(
                    f"Data source with fqn {data_source_fqn} is already associated with "
                    f"collection {collection.name}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Data source with fqn {data_source_fqn} is associated "
                    f"with collection {collection.name}. Delete the necessary collections "
                    f"or unassociate them from the collection(s) before deleting the data source",
                )

        # Delete the data source
        deleted_datasource: Optional[
            PrismaDataSource
        ] = await self.db.datasource.delete(where={"fqn": data_source_fqn})

        if not deleted_datasource:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to delete data source {data_source_fqn!r}. No such record found",
            )

        return DataSource.model_validate(deleted_datasource.model_dump())

    ######
    # DATA INGESTION RUN APIS
    ######
    async def acreate_data_ingestion_run(
        self, data_ingestion_run: CreateDataIngestionRun
    ) -> DataIngestionRun:
        """Create a data ingestion run in the metadata store"""

        run_name = (
            data_ingestion_run.collection_name
            + "-"
            + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
        )
        created_data_ingestion_run = DataIngestionRun(
            name=run_name,
            collection_name=data_ingestion_run.collection_name,
            data_source_fqn=data_ingestion_run.data_source_fqn,
            parser_config=data_ingestion_run.parser_config,
            data_ingestion_mode=data_ingestion_run.data_ingestion_mode,
            status=DataIngestionRunStatus.INITIALIZED,
            raise_error_on_failure=data_ingestion_run.raise_error_on_failure,
        )

        run_data = created_data_ingestion_run.model_dump()
        run_data["parser_config"] = json.dumps(run_data["parser_config"])
        data_ingestion_run: "PrismaDataIngestionRun" = (
            await self.db.ingestionruns.create(data=run_data)
        )
        return DataIngestionRun.model_validate(data_ingestion_run.model_dump())

    async def aget_data_ingestion_run(
        self, data_ingestion_run_name: str, no_cache: bool = False
    ) -> Optional[DataIngestionRun]:
        data_ingestion_run: Optional[
            "PrismaDataIngestionRun"
        ] = await self.db.ingestionruns.find_first(
            where={"name": data_ingestion_run_name}
        )
        logger.info(f"Data ingestion run: {data_ingestion_run}")
        if data_ingestion_run:
            return DataIngestionRun.model_validate(data_ingestion_run.model_dump())
        return None

    async def aget_data_ingestion_runs(
        self, collection_name: str, data_source_fqn: str = None
    ) -> List[DataIngestionRun]:
        """Get all data ingestion runs for a collection"""
        data_ingestion_runs: List[
            "PrismaDataIngestionRun"
        ] = await self.db.ingestionruns.find_many(
            where={"collection_name": collection_name}, order={"id": "desc"}
        )
        return [
            DataIngestionRun.model_validate(data_ir.model_dump())
            for data_ir in data_ingestion_runs
        ]

    async def aupdate_data_ingestion_run_status(
        self, data_ingestion_run_name: str, status: DataIngestionRunStatus
    ) -> DataIngestionRun:
        """Update the status of a data ingestion run"""
        updated_data_ingestion_run: Optional[
            "PrismaDataIngestionRun"
        ] = await self.db.ingestionruns.update(
            where={"name": data_ingestion_run_name}, data={"status": status}
        )
        if not updated_data_ingestion_run:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to update ingestion run {data_ingestion_run_name!r}. No such record found",
            )

        return DataIngestionRun.model_validate(updated_data_ingestion_run.model_dump())

    async def alog_errors_for_data_ingestion_run(
        self, data_ingestion_run_name: str, errors: Dict[str, Any]
    ) -> None:
        """Log errors for the given data ingestion run"""
        updated_data_ingestion_run: Optional[
            "PrismaDataIngestionRun"
        ] = await self.db.ingestionruns.update(
            where={"name": data_ingestion_run_name},
            data={"errors": json.dumps(errors)},
        )
        if not updated_data_ingestion_run:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to update ingestion run {data_ingestion_run_name!r}. No such record found",
            )

    ######
    # RAG APPLICATION APIS
    ######
    async def aget_rag_app(self, app_name: str) -> Optional[RagApplication]:
        """Get a RAG application from the metadata store"""
        rag_app: Optional[
            "PrismaRagApplication"
        ] = await self.db.ragapps.find_first_or_raise(where={"name": app_name})

        return RagApplication.model_validate(rag_app.model_dump())

    async def acreate_rag_app(self, app: RagApplication) -> RagApplication:
        """Create a RAG application in the metadata store"""
        rag_app_data = app.model_dump()
        rag_app_data["config"] = json.dumps(rag_app_data["config"])
        rag_app: "PrismaRagApplication" = await self.db.ragapps.create(
            data=rag_app_data
        )
        return RagApplication.model_validate(rag_app.model_dump())

    async def alist_rag_apps(self) -> List[str]:
        """List all RAG applications from the metadata store"""
        rag_apps: List["PrismaRagApplication"] = await self.db.ragapps.find_many()
        return [rag_app.name for rag_app in rag_apps]

    async def adelete_rag_app(self, app_name: str):
        """Delete a RAG application from the metadata store"""
        deleted_rag_app: Optional[
            "PrismaRagApplication"
        ] = await self.db.ragapps.delete(where={"name": app_name})
        if not deleted_rag_app:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to delete RAG application {app_name!r}. No such record found",
            )


if __name__ == "__main__":
    # initialize the PrismaStore
    prisma_store = PrismaStore.aconnect()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(prisma_store)
