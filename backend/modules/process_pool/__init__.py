import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor

from fastapi import FastAPI

from backend.settings import settings


class AsyncProcessPoolExecutor(ProcessPoolExecutor):
    @staticmethod
    def _async_to_sync(__fn, *args, **kwarg):
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(__fn(*args, **kwarg))
        loop.close()
        return result

    def submit(self, __fn, *args, **kwargs):
        return super().submit(self._async_to_sync, __fn, *args, **kwargs)


process_pool = AsyncProcessPoolExecutor(max_workers=settings.PROCESS_POOL_WORKERS)


@asynccontextmanager
async def process_pool_lifespan_manager(app: FastAPI):
    global process_pool
    yield  # FastAPI runs here
    # Shutdown the ProcessPoolExecutor when the app is shutting down
    process_pool.shutdown(wait=True)
