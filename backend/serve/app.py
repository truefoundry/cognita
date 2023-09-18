import os
from timeit import default_timer as timer

import grpc
import mlflow
import mlfoundry
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from langchain.vectorstores import Qdrant
from servicefoundry import trigger_job
from servicefoundry.langchain import TruefoundryPlaygroundLLM
from servicefoundry.lib.dao.application import get_job_run

from backend.common.db.qdrant import (
    delete_qdrant_collection_if_exists,
    get_qdrant_client,
)
from backend.common.embedder import get_embedder
from backend.common.logger import logger
from backend.serve.base import RepoModel, SearchQuery

# load environment variables
load_dotenv()

# FastAPI Initialization
app = FastAPI(
    title="QA for your own documents",
    summary="Deadpool's favorite app. Nuff said.",
    root_path=os.getenv("TFY_SERVICE_ROOT_PATH"),
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# initialize MLFoundry client
ML_REPO = os.environ["ML_REPO"]

if not ML_REPO:
    raise Exception("MLRepo configuration not provided")

print("Started server")
mlfoundry_client = mlfoundry.get_client()
qdrant_client = get_qdrant_client()


@app.get("/")
async def status():
    return {"status": "ok"}


@app.post("/search")
async def search(request: SearchQuery):
    logger.info(request)
    mlfoundry_run = None
    # Check if mlfoundry repo exists
    try:
        logger.info("Getting mlfoundry run")
        mlfoundry_run = mlfoundry_client.get_run_by_name(ML_REPO, request.repo_name)
    except mlflow.exceptions.RestException as exp:
        if exp.error_code == "RESOURCE_DOES_NOT_EXIST":
            raise HTTPException(status_code=404, detail=str(exp))
        logger.exception(str(exp))
        raise HTTPException(status_code=500, detail=str(exp))
    except Exception as exp:
        logger.exception(str(exp))
        raise HTTPException(status_code=500, detail=str(exp))

    if mlfoundry_run is None:
        raise HTTPException(status_code=400, detail="Repo not found")

    logger.info("Getting mlfoundry params")
    logged_params = mlfoundry_run.get_params()
    DOCUMENT_PROMPT = PromptTemplate(
        input_variables=["page_content"],
        template="<document>{page_content}</document>",
    )
    QA_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template=request.prompt_template,
    )
    try:
        # get the embedders
        logger.info("Getting embedding")
        embeddings = get_embedder(logged_params.get("embedder"), logged_params)
        # initialize the indexed collection
        # qdrandb parameters
        qdrant_db = Qdrant(
            client=qdrant_client,
            collection_name=request.repo_name,
            embeddings=embeddings,
        )
        retriever = qdrant_db.as_retriever()
        retriever.search_kwargs["distance_metric"] = "cos"
        retriever.search_kwargs["fetch_k"] = request.fetch_k
        retriever.search_kwargs["maximal_marginal_relevance"] = request.mmr
        retriever.search_kwargs["k"] = request.k

        # load LLM model
        # model_config = json.loads(request.model_configuration)
        model = TruefoundryPlaygroundLLM(
            model_name=request.model_configuration.name,
            provider=request.model_configuration.provider,
            parameters=request.model_configuration.parameters,
            api_key=os.environ["TFY_API_KEY"],
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

    except grpc._channel._InactiveRpcError as exp:
        if exp.code().name == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=exp.details())
        logger.exception(str(exp))
        raise HTTPException(status_code=500, detail=exp.details())
    except Exception as exp:
        logger.exception(str(exp))
        raise HTTPException(status_code=400, detail=str(exp))
    except:
        logger.exception("Unknown error")
        raise HTTPException(status_code=500, detail="Unknown error")


@app.post("/repo")
async def submit_repo_to_index(repo: RepoModel):
    """
    Trigger the job to index the repo
    """
    result = trigger_job(
        application_fqn=repo.job_fqn,
        params={
            "chunk_size": repo.chunk_size,
            "source_uri": repo.source_uri,
            "ml_repo": ML_REPO,
            "repo_name": repo.repo_name,
            "repo_creds": repo.repo_creds,
            "embedder": repo.embedder,
            "embedder_config": repo.embedder_config,
        },
    )
    logger.info(result)
    return result.jobRunName


@app.get("/repo-status/{jobrun_name}")
async def repo_status(jobrun_name: str, job_fqn: str):
    """
    Get the status of the repo
    Fetch run status to see if the repo has been indexed
    """
    job_run = get_job_run(application_fqn=job_fqn, job_run_name=jobrun_name)
    sfy_job_status = job_run.status

    if sfy_job_status == "SCHEDULED":
        return {"status": "Job Queued"}
    elif sfy_job_status == "FINISHED":
        # Get run name from MLFoundry
        runs = mlfoundry_client.search_runs(
            ml_repo=ML_REPO,
            filter_string="tags.TFY_INTERNAL_JOB_RUN_NAME ='" + jobrun_name + "'",
        )
        runs_list = list(runs)
        assert len(runs_list) == 1
        mlfoundry_run = runs_list[0]
        return {"status": "Finished", "repo_name": mlfoundry_run.run_name}
    elif sfy_job_status == "FAILED":
        return {"status": "Failed"}
    elif sfy_job_status == "RUNNING":
        # Get run status from MLFoundry
        runs = mlfoundry_client.search_runs(
            ml_repo=ML_REPO,
            filter_string="tags.TFY_INTERNAL_JOB_RUN_NAME ='" + jobrun_name + "'",
        )
        runs_list = list(runs)
        logger.info(runs_list)
        if len(runs_list) > 1:
            raise HTTPException(
                status_code=400, detail="Multiple runs found for the given job run name"
            )
        elif len(runs_list) == 0:
            return {"status": "Indexing Job Started"}
        else:
            mlfoundry_run = runs_list[0]
            metrics = mlfoundry_run.get_metrics(
                metric_names=["processing_time", "num_files"]
            )
            files_indexed = 0
            num_files = 0
            progress = 0
            if metrics.get("processing_time"):
                files_indexed = metrics.get("processing_time")[-1].step + 1
                num_files = metrics.get("num_files")[-1].value
            if num_files > 0:
                progress = (files_indexed * 100) / num_files
            return {
                "status": "Running",
                "files_indexed": files_indexed,
                "num_files": num_files,
                "progress": progress,
                "repo_name": mlfoundry_run.run_name,
            }


@app.get("/repos")
async def repos():
    start_time = timer()
    runs = mlfoundry_client.search_runs(
        ml_repo=ML_REPO,
        filter_string="params.dry_run ='False' and params.source_uri !=''",
    )
    repo_names = []
    repo_details = []
    for run in runs:
        repo_names.append(run.run_name)
        tags = run.get_tags()
        params = run.get_params()
        repo_details.append(
            {
                "repo_name": run.run_name,
                "job_name": tags.get("TFY_INTERNAL_JOB_RUN_NAME"),
                "source_uri": params.get("source_uri"),
                "embedder": params.get("embedder"),
                "chunk_size": params.get("chunk_size"),
            }
        )
    logger.debug("Time taken: " + str(timer() - start_time))
    return {"output": repo_names, "repos": repo_details}


@app.delete("/repo/{repo_name}")
async def delete_repo(repo_name: str):
    try:
        mlfoundry_run = mlfoundry_client.get_run_by_name(
            ml_repo=ML_REPO, run_name=repo_name
        )
        logger.info("deleting mlfoundry run: %s", mlfoundry_run.fqn)
        if mlfoundry_run:
            mlfoundry_run.delete()
        logger.info("deleting qdrant collection")
        delete_qdrant_collection_if_exists(repo_name)
        return {"status": "ok"}
    except mlflow.exceptions.RestException as exp:
        if exp.error_code == "RESOURCE_DOES_NOT_EXIST":
            logger.info("mlfoundry run not found")
            return {"status": "ok"}
        logger.exception(str(exp))
        raise HTTPException(status_code=500, detail=str(exp))
    except grpc._channel._InactiveRpcError as exp:
        if exp.code().name == "NOT_FOUND":
            logger.info("collection not found")
            return {"status": "ok"}
        logger.exception(str(exp))
        raise HTTPException(status_code=500, detail=exp.details())
    except Exception as exp:
        logger.exception(str(exp))
        raise HTTPException(status_code=400, detail=str(exp))
    except:
        logger.exception("Unknown error")
        raise HTTPException(status_code=500, detail="Unknown error")
