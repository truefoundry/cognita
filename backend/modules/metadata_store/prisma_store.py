import asyncio
import json
import os
import random
import shutil
import string
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from fastapi import HTTPException
from prisma import Prisma

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
    def __init__(self, *args, db, **kwargs) -> None:
        self.db = db
        super().__init__(*args, **kwargs)

    @classmethod
    async def aconnect(cls, **kwargs):
        try:
            db = Prisma()
            await db.connect()
            logger.info(f"Connected to Prisma")
            return cls(db=db, **kwargs)
        except Exception as e:
            logger.exception(f"Failed to connect to Prisma: {e}")
            raise HTTPException(status_code=500, detail="Failed to connect to Prisma")

    ######
    # COLLECTIONS APIS
    ######

    async def aget_collection_by_name(
        self, collection_name: str, no_cache: bool = True
    ) -> Optional[Collection]:
        try:
            collection: Optional[
                "PrismaCollection"
            ] = await self.db.collection.find_first(where={"name": collection_name})
            if collection:
                return Collection.model_validate(collection.model_dump())
            return None
        except Exception as e:
            logger.exception(f"Failed to get collection by name: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to get collection by name"
            )

    async def acreate_collection(self, collection: CreateCollection) -> Collection:
        try:
            existing_collection = await self.aget_collection_by_name(collection.name)
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=e)

        if existing_collection:
            logger.error(f"Collection with name {collection.name} already exists")
            raise HTTPException(
                status_code=400,
                detail=f"Collection with name {collection.name} already exists",
            )

        try:
            logger.info(f"Creating collection: {collection.model_dump()}")
            collection_data = collection.model_dump()
            collection_data["embedder_config"] = json.dumps(
                collection_data["embedder_config"]
            )
            collection: "PrismaCollection" = await self.db.collection.create(
                data=collection_data
            )
            return Collection.model_validate(collection.model_dump())
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

    async def aget_retrieve_collection_by_name(
        self, collection_name: str, no_cache: bool = True
    ) -> Optional[Collection]:
        collection: "PrismaCollection" = await self.aget_collection_by_name(
            collection_name, no_cache
        )
        return Collection.model_validate(collection.model_dump())

    async def aget_collections(self) -> List[Collection]:
        try:
            collections: List["PrismaCollection"] = await self.db.collection.find_many(
                order={"id": "desc"}
            )
            return [Collection.model_validate(c.model_dump()) for c in collections]
        except Exception as e:
            logger.exception(f"Failed to get collections: {e}")
            raise HTTPException(status_code=500, detail="Failed to get collections")

    async def alist_collections(self) -> List[str]:
        try:
            collections = await self.aget_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            logger.exception(f"Failed to list collections: {e}")
            raise HTTPException(status_code=500, detail="Failed to list collections")

    async def adelete_collection(self, collection_name: str, include_runs=False):
        try:
            deleted_collection: Optional[
                "PrismaCollection"
            ] = await self.db.collection.delete(where={"name": collection_name})
            if not deleted_collection:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to delete collection {collection_name!r}. No such record found",
                )
            if include_runs:
                try:
                    _deleted_count = await self.db.ingestionruns.delete_many(
                        where={"collection_name": collection_name}
                    )
                except Exception as e:
                    logger.exception(f"Failed to delete data ingestion runs: {e}")
        except Exception as e:
            logger.exception(f"Failed to delete collection: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete collection")

    ######
    # DATA SOURCE APIS
    ######
    async def aget_data_source_from_fqn(self, fqn: str) -> Optional[DataSource]:
        try:
            data_source: Optional[
                "PrismaDataSource"
            ] = await self.db.datasource.find_first(where={"fqn": fqn})
            if data_source:
                return DataSource.model_validate(data_source.model_dump())
            return None
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

    async def acreate_data_source(self, data_source: CreateDataSource) -> DataSource:
        try:
            existing_data_source = await self.aget_data_source_from_fqn(data_source.fqn)
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

        if existing_data_source:
            logger.exception(f"Data source with fqn {data_source.fqn} already exists")
            raise HTTPException(
                status_code=400,
                detail=f"Data source with fqn {data_source.fqn} already exists",
            )

        try:
            data = data_source.model_dump()
            data["metadata"] = json.dumps(data["metadata"])
            data_source: "PrismaDataSource" = await self.db.datasource.create(data)
            logger.info(f"Created data source: {data_source}")
            return DataSource.model_validate(data_source.model_dump())
        except Exception as e:
            logger.exception(f"Failed to create data source: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

    async def aget_data_sources(self) -> List[DataSource]:
        try:
            data_sources: List["PrismaDataSource"] = await self.db.datasource.find_many(
                order={"id": "desc"}
            )
            return [DataSource.model_validate(ds.model_dump()) for ds in data_sources]
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

    async def aassociate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_association: AssociateDataSourceWithCollection,
    ) -> Collection:
        try:
            existing_collection = await self.aget_collection_by_name(collection_name)
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

        if not existing_collection:
            logger.error(f"Collection with name {collection_name} does not exist")
            raise HTTPException(
                status_code=400,
                detail=f"Collection with name {collection_name} does not exist",
            )

        try:
            data_source = await self.aget_data_source_from_fqn(
                data_source_association.data_source_fqn
            )
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

        if not data_source:
            logger.error(
                f"Data source with fqn {data_source_association.data_source_fqn} does not exist"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Data source with fqn {data_source_association.data_source_fqn} does not exist",
            )

        logger.info(f"Data source to associate: {data_source}")
        try:
            # Append datasource to existing collection
            existing_collection_associated_data_sources = (
                existing_collection.associated_data_sources
            )
            logger.info(
                f"Existing associated data sources: {existing_collection_associated_data_sources}"
            )

            data_src_to_associate = AssociatedDataSources(
                data_source_fqn=data_source_association.data_source_fqn,
                parser_config=data_source_association.parser_config,
                data_source=data_source,
            )

            if existing_collection_associated_data_sources:
                existing_collection_associated_data_sources[
                    data_src_to_associate.data_source_fqn
                ] = data_src_to_associate
            else:
                existing_collection_associated_data_sources = {
                    data_src_to_associate.data_source_fqn: data_src_to_associate
                }

            logger.info(existing_collection_associated_data_sources)
            associated_data_sources: Dict[str, Dict[str, Any]] = {}
            for (
                data_source_fqn,
                data_source,
            ) in existing_collection_associated_data_sources.items():
                associated_data_sources[data_source_fqn] = data_source.model_dump()

            updated_collection: Optional[
                "PrismaCollection"
            ] = await self.db.collection.update(
                where={"name": collection_name},
                data={"associated_data_sources": json.dumps(associated_data_sources)},
            )
            if not updated_collection:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to associate data source with collection {collection_name!r}. "
                    f"No such record found",
                )
            return Collection.model_validate(updated_collection.model_dump())

        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error: {e}",
            )

    async def aunassociate_data_source_with_collection(
        self, collection_name: str, data_source_fqn: str
    ) -> Collection:
        try:
            collection: Collection = await self.aget_collection_by_name(collection_name)
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

        if not collection:
            logger.error(f"Collection with name {collection_name} does not exist")
            raise HTTPException(
                status_code=400,
                detail=f"Collection with name {collection_name} does not exist",
            )

        try:
            data_source = await self.aget_data_source_from_fqn(data_source_fqn)
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

        if not data_source:
            logger.error(f"Data source with fqn {data_source_fqn} does not exist")
            raise HTTPException(
                status_code=400,
                detail=f"Data source with fqn {data_source_fqn} does not exist",
            )

        associated_data_sources = collection.associated_data_sources
        if not associated_data_sources:
            logger.error(
                f"No associated data sources found for collection {collection_name}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"No associated data sources found for collection {collection_name}",
            )
        if data_source_fqn not in associated_data_sources:
            logger.error(
                f"Data source with fqn {data_source_fqn} not associated with collection {collection_name}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Data source with fqn {data_source_fqn} not associated with collection {collection_name}",
            )
        associated_data_sources.pop(data_source_fqn, None)

        try:
            # Convert associated_data_sources of type [dict, AssociatedDataSources] to [dict, dict]
            updated_associated_data_sources: Dict[str, Dict[str, Any]] = {}
            for (
                data_source_fqn,
                data_source,
            ) in associated_data_sources.items():
                updated_associated_data_sources[
                    data_source_fqn
                ] = data_source.model_dump()

            updated_collection: Optional[
                "PrismaCollection"
            ] = await self.db.collection.update(
                where={"name": collection_name},
                data={
                    "associated_data_sources": json.dumps(
                        updated_associated_data_sources
                    )
                },
            )
            if not updated_collection:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to unassociate data source from collection. "
                    f"No collection found with name {collection_name}",
                )
            logger.info(f"Updated collection: {updated_collection}")
            return Collection.model_validate(updated_collection.model_dump())
        except Exception as e:
            logger.exception(f"Failed to unassociate data source with collection: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to unassociate data source with collection",
            )

    async def alist_data_sources(
        self,
    ) -> List[Dict[str, str]]:
        try:
            data_sources = await self.aget_data_sources()
            return [data_source.model_dump() for data_source in data_sources]
        except Exception as e:
            logger.exception(f"Failed to list data sources: {e}")
            raise HTTPException(status_code=500, detail="Failed to list data sources")

    async def adelete_data_source(self, data_source_fqn: str) -> None:
        # Check if data source exists if not raise an error
        try:
            data_source = await self.aget_data_source_from_fqn(data_source_fqn)
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

        if not data_source:
            logger.error(f"Data source with fqn {data_source_fqn} does not exist")
            raise HTTPException(
                status_code=400,
                detail=f"Data source with fqn {data_source_fqn} does not exist",
            )

        # Check if data source is associated with any collection
        try:
            collections = await self.aget_collections()
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

        for collection in collections:
            associated_data_sources = collection.associated_data_sources
            if associated_data_sources and data_source_fqn in associated_data_sources:
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
        try:
            logger.info(f"Data source to delete: {data_source}")
            deleted_datasource: Optional[
                PrismaDataSource
            ] = await self.db.datasource.delete(where={"fqn": data_source.fqn})
            if not deleted_datasource:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to delete data source {data_source.fqn!r}. No such record found",
                )
            # Delete the data from `/users_data` directory if data source is of type `localdir`
            if data_source.type == "localdir":
                data_source_uri = data_source.uri
                # data_source_uri is of the form: `/app/users_data/folder_name`
                folder_name = data_source_uri.split("/")[-1]
                folder_path = os.path.join(settings.LOCAL_DATA_DIRECTORY, folder_name)
                logger.info(
                    f"Deleting folder: {folder_path}, path exists: {os.path.exists(folder_path)}"
                )
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                else:
                    logger.error(f"Folder does not exist: {folder_path}")

        except Exception as e:
            logger.exception(f"Failed to delete data source: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete data source")

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

        try:
            run_data = created_data_ingestion_run.model_dump()
            run_data["parser_config"] = json.dumps(run_data["parser_config"])
            data_ingestion_run: "PrismaDataIngestionRun" = (
                await self.db.ingestionruns.create(data=run_data)
            )
            return DataIngestionRun.model_validate(data_ingestion_run.model_dump())
        except Exception as e:
            logger.exception(f"Failed to create data ingestion run: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create data ingestion run: {e}"
            )

    async def aget_data_ingestion_run(
        self, data_ingestion_run_name: str, no_cache: bool = False
    ) -> Optional[DataIngestionRun]:
        try:
            data_ingestion_run: Optional[
                "PrismaDataIngestionRun"
            ] = await self.db.ingestionruns.find_first(
                where={"name": data_ingestion_run_name}
            )
            logger.info(f"Data ingestion run: {data_ingestion_run}")
            if data_ingestion_run:
                return DataIngestionRun.model_validate(data_ingestion_run.model_dump())
            return None
        except Exception as e:
            logger.exception(f"Failed to get data ingestion run: {e}")
            raise HTTPException(status_code=500, detail=f"{e}")

    async def aget_data_ingestion_runs(
        self, collection_name: str, data_source_fqn: str = None
    ) -> List[DataIngestionRun]:
        """Get all data ingestion runs for a collection"""
        try:
            data_ingestion_runs: List[
                "PrismaDataIngestionRun"
            ] = await self.db.ingestionruns.find_many(
                where={"collection_name": collection_name}, order={"id": "desc"}
            )
            return [
                DataIngestionRun.model_validate(data_ir.model_dump())
                for data_ir in data_ingestion_runs
            ]
        except Exception as e:
            logger.exception(f"Failed to get data ingestion runs: {e}")
            raise HTTPException(status_code=500, detail=f"{e}")

    async def aupdate_data_ingestion_run_status(
        self, data_ingestion_run_name: str, status: DataIngestionRunStatus
    ) -> DataIngestionRun:
        """Update the status of a data ingestion run"""
        try:
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

            return DataIngestionRun.model_validate(
                updated_data_ingestion_run.model_dump()
            )
        except Exception as e:
            logger.exception(f"Failed to update data ingestion run status: {e}")
            raise HTTPException(status_code=500, detail=f"{e}")

    async def alog_errors_for_data_ingestion_run(
        self, data_ingestion_run_name: str, errors: Dict[str, Any]
    ) -> None:
        """Log errors for the given data ingestion run"""
        try:
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
        except Exception as e:
            logger.exception(
                f"Failed to log errors data ingestion run {data_ingestion_run_name}: {e}"
            )
            raise HTTPException(status_code=500, detail=f"{e}")

    ######
    # RAG APPLICATION APIS
    ######
    async def aget_rag_app(self, app_name: str) -> Optional[RagApplication]:
        """Get a RAG application from the metadata store"""
        try:
            rag_app: Optional[
                "PrismaRagApplication"
            ] = await self.db.ragapps.find_first(where={"name": app_name})
            if rag_app:
                return RagApplication.model_validate(rag_app.model_dump())
            return None
        except Exception as e:
            logger.exception(f"Failed to get RAG application by name: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to get RAG application by name"
            )

    async def acreate_rag_app(self, app: RagApplication) -> RagApplication:
        """Create a RAG application in the metadata store"""
        try:
            existing_app = await self.aget_rag_app(app.name)
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=e)

        if existing_app:
            logger.error(f"RAG application with name {app.name} already exists")
            raise HTTPException(
                status_code=400,
                detail=f"RAG application with name {app.name} already exists",
            )

        try:
            logger.info(f"Creating RAG application: {app.model_dump()}")
            rag_app_data = app.model_dump()
            rag_app_data["config"] = json.dumps(rag_app_data["config"])
            rag_app: "PrismaRagApplication" = await self.db.ragapps.create(
                data=rag_app_data
            )
            return RagApplication.model_validate(rag_app.model_dump())
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {e}")

    async def alist_rag_apps(self) -> List[str]:
        """List all RAG applications from the metadata store"""
        try:
            rag_apps: List["PrismaRagApplication"] = await self.db.ragapps.find_many()
            return [rag_app.name for rag_app in rag_apps]
        except Exception as e:
            logger.exception(f"Failed to list RAG applications: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to list RAG applications"
            )

    async def adelete_rag_app(self, app_name: str):
        """Delete a RAG application from the metadata store"""
        try:
            deleted_rag_app: Optional[
                "PrismaRagApplication"
            ] = await self.db.ragapps.delete(where={"name": app_name})
            if not deleted_rag_app:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to delete RAG application {app_name!r}. No such record found",
                )
        except Exception as e:
            logger.exception(f"Failed to delete RAG application: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to delete RAG application"
            )


if __name__ == "__main__":
    # initialize the PrismaStore
    prisma_store = PrismaStore.aconnect()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(prisma_store)
