import json
from typing import Optional

import mlfoundry
import requests
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from mlfoundry.artifact.truefoundry_artifact_repo import (
    ArtifactIdentifier,
    MlFoundryArtifactsRepository,
)
from servicefoundry import trigger_job

from backend.indexer.indexer import trigger_job_locally
from backend.modules.embedder import get_embedder
from backend.modules.llms.truefoundry_llm import TrueFoundryLLMGateway
from backend.modules.metadata_store import get_metadata_store_client
from backend.modules.metadata_store.models import (
    CollectionCreate,
    CollectionIndexerJobRunCreate,
    CollectionIndexerJobRunStatus,
)
from backend.modules.retrieval_chains import get_retrieval_chain
from backend.modules.retrievers import get_retriever
from backend.modules.vector_db import get_vector_db_client
from backend.settings import settings
from backend.utils.base import (
    AddDocuments,
    CreateCollection,
    IndexerConfig,
    ModelType,
    SearchQuery,
    UploadToDataDirectoryDto,
)
from backend.utils.logger import logger

metadata_store_client = get_metadata_store_client(config=settings.METADATA_STORE_CONFIG)

# FastAPI Initialization
app = FastAPI(
    title="Backend for RAG",
    root_path=settings.TFY_SERVICE_ROOT_PATH,
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def status():
    return JSONResponse(content={"status": "ok"})


@app.get("/collections")
async def get_collections():
    try:
        vector_db_client = get_vector_db_client(config=settings.VECTOR_DB_CONFIG)
        collection_names = vector_db_client.get_collections()
        collections = metadata_store_client.get_collections(
            names=collection_names, include_runs=False
        )
        return JSONResponse(
            content={"collections": [obj.dict() for obj in collections]}
        )
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@app.post("/collections")
async def create_collection(request: CreateCollection):
    try:
        existing_collection = metadata_store_client.get_collection_by_name(
            collection_name=request.name
        )
        if existing_collection:
            return HTTPException(
                status_code=400,
                detail=f"Collection with name {request.name} already exists.",
            )
        collection = metadata_store_client.create_collection(
            CollectionCreate(
                name=request.name,
                description=request.description,
                embedder_config=request.embedder_config,
                chunk_size=request.chunk_size,
            )
        )
        vector_db_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=request.name
        )
        vector_db_client.create_collection(get_embedder(request.embedder_config))
        return JSONResponse(content={"collection": collection.dict()}, status_code=201)
    except Exception as exp:
        try:
            metadata_store_client.delete_collection(collection_name=request.name)
        except Exception as e:
            logger.exception(e)
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@app.post("/collections/{collection_name}/add_docs")
async def add_documents_to_collection(
    request: AddDocuments, collection_name: str = Path(title="Collection name")
):
    try:
        collection = metadata_store_client.get_collection_by_name(
            collection_name=collection_name
        )
        if not collection:
            return HTTPException(
                status_code=404,
                detail=f"Collection with name {collection_name} does not exist.",
            )
        current_indexer_job_run = metadata_store_client.get_current_indexer_job_run(
            collection_name=collection_name
        )
        if (
            not request.force
            and current_indexer_job_run
            and current_indexer_job_run.status
            not in [
                CollectionIndexerJobRunStatus.COMPLETED,
                CollectionIndexerJobRunStatus.FAILED,
            ]
        ):
            return HTTPException(
                status_code=400,
                detail=f"Collection with name {collection_name} already has an active indexer job run with status {current_indexer_job_run.status.value}. Please wait for it to complete.",
            )

        indexer_job_run = metadata_store_client.create_collection_indexer_job_run(
            collection_name=collection_name,
            indexer_job_run=CollectionIndexerJobRunCreate(
                data_source=request.data_source,
                parser_config=request.parser_config,
            ),
        )

        if settings.DEBUG_MODE:
            await trigger_job_locally(
                inputs=IndexerConfig(
                    collection_name=collection_name,
                    indexer_job_run_name=indexer_job_run.name,
                    data_source=request.data_source,
                    chunk_size=collection.chunk_size,
                    embedder_config=collection.embedder_config,
                    parser_config=request.parser_config,
                    vector_db_config=settings.VECTOR_DB_CONFIG,
                    metadata_store_config=settings.METADATA_STORE_CONFIG,
                    embedding_cache_config=settings.EMBEDDING_CACHE_CONFIG,
                )
            )
        else:
            trigger_job(
                application_fqn=settings.JOB_FQN,
                component_name=settings.JOB_COMPONENT_NAME,
                params={
                    "collection_name": collection_name,
                    "indexer_job_run_name": indexer_job_run.name,
                    "data_source": json.dumps(request.data_source.dict()),
                    "chunk_size": str(collection.chunk_size),
                    "embedder_config": json.dumps(collection.embedder_config.dict()),
                    "parser_config": json.dumps(request.parser_config.dict()),
                    "vector_db_config": json.dumps(settings.VECTOR_DB_CONFIG.dict()),
                    "metadata_store_config": json.dumps(
                        settings.METADATA_STORE_CONFIG.dict()
                    ),
                    **(
                        {
                            "embedding_cache_config": json.dumps(
                                settings.EMBEDDING_CACHE_CONFIG.dict()
                            )
                        }
                        if settings.EMBEDDING_CACHE_CONFIG
                        else {}
                    ),
                },
            )
        return JSONResponse(
            status_code=201, content={"indexer_job_run": indexer_job_run.dict()}
        )
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@app.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str = Path(title="Collection name")):
    try:
        vector_db_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=collection_name
        )
        vector_db_client.delete_collection()
        metadata_store_client.delete_collection(collection_name, include_runs=True)
        return JSONResponse(content={"deleted": True})
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@app.get("/collections/{collection_name}/status")
async def get_collection_status(collection_name: str = Path(title="Collection name")):
    collection = metadata_store_client.get_collection_by_name(
        collection_name=collection_name
    )

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    current_indexer_job_run = metadata_store_client.get_current_indexer_job_run(
        collection_name=collection_name
    )

    if current_indexer_job_run is None:
        return JSONResponse(
            content={"status": "MISSING", "message": "No indexer job runs found"}
        )

    return JSONResponse(
        content={
            "status": current_indexer_job_run.status.value,
            "message": f"Indexer job run {current_indexer_job_run.name} in {current_indexer_job_run.status.value}. Check logs for more details.",
        }
    )


@app.post("/search")
async def search(request: SearchQuery):
    logger.info(request)
    # Get collection
    collection = metadata_store_client.get_collection_by_name(request.collection_name)

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    try:
        # Vector Store Client
        vector_db_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=request.collection_name
        )
        # Model to use for chat
        llm = TrueFoundryLLMGateway(
            model=request.model_configuration.name,
            model_parameters=request.model_configuration.parameters,
        )
        logger.info(f"Loaded TrueFoundry LLM model {request.model_configuration.name}")

        # get vector store
        vector_store = vector_db_client.get_vector_store(
            embeddings=get_embedder(collection.embedder_config),
        )

        # get retriever
        retriever = get_retriever(
            vectorstore=vector_store,
            retriever_config=request.retriever_config,
            llm=llm,
        )

        DOCUMENT_PROMPT = PromptTemplate(
            input_variables=["page_content"],
            template="<document>{page_content}</document>",
        )
        QA_PROMPT = PromptTemplate(
            input_variables=["context", "question"],
            template=request.prompt_template,
        )
        # Chain to get output for given query from docs using llm
        retrieval_chain = get_retrieval_chain(
            chain_name=request.retrieval_chain_name,
            retriever=retriever,
            llm=llm,
            combine_documents_chain=load_qa_chain(
                llm=llm,
                chain_type="stuff",
                prompt=QA_PROMPT,
                document_variable_name="context",
                document_prompt=DOCUMENT_PROMPT,
                verbose=True,
            ),
            return_source_documents=True,
            verbose=True,
        )

        outputs = retrieval_chain({"query": request.query})

        return {
            "answer": outputs["result"],
            "docs": outputs.get("source_documents") or [],
        }

    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@app.post("/upload-to-data-directory")
async def upload_to_data_directory(req: UploadToDataDirectoryDto):
    if settings.METADATA_STORE_CONFIG.provider != "mlfoundry":
        raise Exception("API only supported for metadata store provider: mlfoundry")
    mlfoundry_client = mlfoundry.get_client()

    # Create a new data directory.
    dataset = mlfoundry_client.create_data_directory(
        settings.METADATA_STORE_CONFIG.config.get("ml_repo_name"), req.collection_name
    )

    artifact_repo = MlFoundryArtifactsRepository(
        artifact_identifier=ArtifactIdentifier(dataset_fqn=dataset.fqn),
        mlflow_client=mlfoundry_client.mlflow_client,
    )

    urls = artifact_repo.get_signed_urls_for_write(
        artifact_identifier=ArtifactIdentifier(dataset_fqn=dataset.fqn),
        paths=req.filepaths,
    )
    data = [url.dict() for url in urls]
    return JSONResponse(
        content={"data": data, "data_directory_fqn": dataset.fqn},
    )


@app.get("/models")
async def get_enabled_models(
    model_type: Optional[ModelType] = Query(default=None),
):
    url = f"{settings.TFY_LLM_GATEWAY_ENDPOINT}/api/model/enabled{f'?model_types={model_type.value}' if model_type else ''}"
    headers = {"Authorization": f"Bearer {settings.TFY_API_KEY}"}
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
    except Exception as ex:
        raise Exception(f"Error fetching the models: {ex}") from ex
    data: dict[str, dict[str, list[dict]]] = response.json()
    enabled_models = []
    for provider_accounts in data.values():
        for models in provider_accounts.values():
            enabled_models.extend(models)

    return JSONResponse(
        content={"models": enabled_models},
    )
