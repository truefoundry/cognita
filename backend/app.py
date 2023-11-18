import json
import orjson
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import RetrievalQA
from backend.settings import settings
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from servicefoundry import trigger_job
from backend.indexer import trigger_job_locally
from backend.base import (
    VectorDBConfig,
    CreateCollection,
    AddDocuments,
    SearchQuery,
    IndexConfig,
)
from backend.logger import logger
from backend.modules.embedder import get_embedder
from backend.modules.vector_db import get_vector_db_client
from backend.modules.metadata_store import get_metadata_store_client
from backend.modules.metadata_store.models import (
    CollectionCreate,
    CollectionIndexerJobRunCreate,
)
from backend.modules.llms.tfy_playground_llm import TfyPlaygroundLLM


VECTOR_DB_CONFIG = VectorDBConfig.parse_obj(orjson.loads(settings.VECTOR_DB_CONFIG))
metadata_store_client = get_metadata_store_client(settings.METADATA_STORE_TYPE)

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
        collections = metadata_store_client.get_collections(include_runs=True)
        return JSONResponse(
            content={"collections": [obj.dict() for obj in collections]}
        )
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@app.post("/collections")
async def create_collection(request: CreateCollection):
    try:
        collection = metadata_store_client.create_collection(
            CollectionCreate(
                name=request.name,
                description=request.description,
                embedder_config=request.embedder_config,
            )
        )
        vector_db_client = get_vector_db_client(
            config=VECTOR_DB_CONFIG, collection_name=request.name
        )
        vector_db_client.create_collection(get_embedder(request.embedder_config))
        return JSONResponse(content={"collection": collection.dict()}, status_code=201)
    except Exception as exp:
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
            raise HTTPException(
                status_code=404,
                detail=f"Collection with name {collection_name} does not exist.",
            )
        indexer_job_run = metadata_store_client.create_collection_indexer_job_run(
            collection_name=collection_name,
            indexer_job_run=CollectionIndexerJobRunCreate(
                knowledge_source=request.knowledge_source,
                parser_config=request.parser_config,
            ),
        )

        if settings.DEBUG_MODE:
            await trigger_job_locally(
                inputs=IndexConfig(
                    collection_name=collection_name,
                    indexer_job_run_name=indexer_job_run.name,
                    knowledge_source=request.knowledge_source,
                    chunk_size=request.chunk_size,
                    embedder_config=collection.embedder_config,
                    parser_config=request.parser_config,
                    vector_db_config=VECTOR_DB_CONFIG,
                )
            )
        else:
            trigger_job(
                application_fqn=settings.JOB_FQN,
                params={
                    "collection_name": collection_name,
                    "indexer_job_run_name": indexer_job_run.name,
                    "knowledge_source": json.dumps(request.knowledge_source.dict()),
                    "chunk_size": str(request.chunk_size),
                    "embedder_config": json.dumps(collection.embedder_config.dict()),
                    "parser_config": json.dumps(request.parser_config.dict()),
                    "vector_db_config": json.dumps(VECTOR_DB_CONFIG.dict()),
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
            config=VECTOR_DB_CONFIG, collection_name=collection_name
        )
        vector_db_client.delete_collection()
        metadata_store_client.delete_collection(collection_name)
        return JSONResponse(content={"deleted": True})
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@app.get("/collections/{collection_name}/status")
async def get_collection_status(collection_name: str = Path(title="Collection name")):
    collection = metadata_store_client.get_collection_by_name(
        collection_name=collection_name, include_runs=True
    )

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    if len(collection.indexer_job_runs) == 0:
        return JSONResponse(
            content={"status": "MISSING", "message": "No indexer job runs found"}
        )
    latest_indexer_job_run = collection.indexer_job_runs[-1]
    return JSONResponse(
        content={
            "status": latest_indexer_job_run.status.value,
            "message": f"Indexer job run {latest_indexer_job_run.name} in {latest_indexer_job_run.status.value}. Check logs for more details.",
        }
    )


@app.post("/search")
async def search(request: SearchQuery):
    logger.info(request)
    # Get collection
    collection = metadata_store_client.get_collection_by_name(request.collection_name)

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    DOCUMENT_PROMPT = PromptTemplate(
        input_variables=["page_content"],
        template="<document>{page_content}</document>",
    )
    QA_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template=request.prompt_template,
    )
    try:
        vector_db_client = get_vector_db_client(
            config=VECTOR_DB_CONFIG, collection_name=request.collection_name
        )
        retriever = vector_db_client.get_retriver(
            get_embedder(collection.embedder_config)
        )
        # retriever.search_kwargs["distance_metric"] = "cos"
        # retriever.search_kwargs["fetch_k"] = request.fetch_k
        # retriever.search_kwargs["maximal_marginal_relevance"] = request.mmr
        retriever.search_kwargs["k"] = request.k

        # load LLM model
        # model_config = json.loads(request.model_configuration)
        model = TfyPlaygroundLLM(
            model_name=request.model_configuration.name,
            parameters=request.model_configuration.parameters,
            api_key=settings.TFY_API_KEY,
        )
        # retrieval QA chain
        logger.info("Loading QA chain")
        qa = RetrievalQA(
            combine_documents_chain=load_qa_chain(
                llm=model,
                chain_type="stuff",
                prompt=QA_PROMPT,
                document_variable_name="context",
                document_prompt=DOCUMENT_PROMPT,
                verbose=True,
            ),
            retriever=retriever,
            return_source_documents=True,
            verbose=True,
        )
        logger.info("Making query chain")
        outputs = qa({"query": request.query})

        # prepare the final prompt for debug
        final_prompt = request.prompt_template.format(
            question=request.query,
            context=" ".join(
                [tx.page_content for tx in outputs.get("source_documents")]
            ),
        )
        if request.debug:
            response = {
                "answer": outputs["result"],
                "docs": outputs.get("source_documents") or [],
                "prompt": final_prompt,
            }
        else:
            response = {
                "answer": outputs["result"],
                "docs": outputs.get("source_documents") or [],
            }

        return response

    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))
