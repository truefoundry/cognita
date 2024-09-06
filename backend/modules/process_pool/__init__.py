from fastapi import FastAPI
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor

from backend.settings import settings

process_pool = ProcessPoolExecutor(max_workers=settings.PROCESS_POOL_WORKERS)

@asynccontextmanager
async def process_pool_lifespan_manager(app: FastAPI):
    global process_pool
    yield  # FastAPI runs here
    # Shutdown the ProcessPoolExecutor when the app is shutting down
    process_pool.shutdown(wait=True)