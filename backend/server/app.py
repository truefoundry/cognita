import asyncio
import multiprocessing as mp
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prisma.errors import RecordNotFoundError, UniqueViolationError

from backend.logger import logger
from backend.modules.query_controllers.query_controller import QUERY_CONTROLLER_REGISTRY
from backend.server.routers.collection import router as collection_router
from backend.server.routers.components import router as components_router
from backend.server.routers.data_source import router as datasource_router
from backend.server.routers.internal import router as internal_router
from backend.server.routers.rag_apps import router as rag_apps_router
from backend.settings import settings
from backend.utils import AsyncProcessPoolExecutor


@asynccontextmanager
async def _process_pool_lifespan_manager(app: FastAPI):
    app.state.process_pool = None
    if settings.PROCESS_POOL_WORKERS > 0:
        app.state.process_pool = AsyncProcessPoolExecutor(
            max_workers=settings.PROCESS_POOL_WORKERS,
            # Setting to spawn because we don't want to fork - it can cause issues with the event loop
            mp_context=mp.get_context("spawn"),
        )

        async def check_pool_health():
            while True:
                try:
                    # Submit a simple task to check if the pool is responsive
                    app.state.process_pool.submit(asyncio.sleep, 0)
                except Exception as e:
                    logger.error(f"Process pool health check failed: {e}")
                    await restart_pool()
                await asyncio.sleep(5)  # Check every 5 seconds

        async def restart_pool():
            logger.info("Restarting the process pool")
            app.state.process_pool.shutdown(wait=True)
            app.state.process_pool = AsyncProcessPoolExecutor(
                max_workers=settings.PROCESS_POOL_WORKERS
            )

        health_check_task = asyncio.create_task(check_pool_health())
    yield  # FastAPI runs here
    if app.state.process_pool is not None:
        health_check_task.cancel()
        logger.info("Shutting down the process pool")
        app.state.process_pool.shutdown(wait=True)


# FastAPI Initialization
app = FastAPI(
    title="Backend for RAG",
    root_path=settings.TFY_SERVICE_ROOT_PATH,
    docs_url="/",
    lifespan=_process_pool_lifespan_manager,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def catch_exceptions_middleware(_request: Request, exc: Exception):
    logger.exception(exc)
    return JSONResponse(
        content={"error": f"An unexpected error occurred: {str(exc)}"}, status_code=500
    )


@app.exception_handler(RecordNotFoundError)
async def catch_exceptions_middleware(_request: Request, exc: RecordNotFoundError):
    logger.exception(exc)
    return JSONResponse(
        content={"error": f"Record not found: {str(exc)}"}, status_code=404
    )


@app.exception_handler(UniqueViolationError)
async def catch_exceptions_middleware(_request: Request, exc: UniqueViolationError):
    logger.exception(exc)
    return JSONResponse(
        content={"error": f"Record already exists: {str(exc)}"}, status_code=400
    )


@app.get("/health-check")
def status():
    return JSONResponse(content={"status": "OK"})


app.include_router(components_router)
app.include_router(datasource_router)
app.include_router(rag_apps_router)
app.include_router(collection_router)
app.include_router(internal_router)

# Register Query Controllers dynamically as FastAPI routers
for cls in QUERY_CONTROLLER_REGISTRY.values():
    router: APIRouter = cls.get_router()
    app.include_router(router)
