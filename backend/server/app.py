from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    app.state.process_pool = AsyncProcessPoolExecutor(
        max_workers=settings.PROCESS_POOL_WORKERS
    )
    yield  # FastAPI runs here
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
