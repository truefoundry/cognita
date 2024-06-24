import asyncio
import zipfile
from concurrent.futures import Executor
from contextvars import copy_context
from functools import partial
from typing import Callable, Optional, TypeVar, cast

from typing_extensions import ParamSpec

P = ParamSpec("P")
T = TypeVar("T")


def flatten(dct, sub_dct_key_name, prefix=None):
    prefix = prefix or f"{sub_dct_key_name}."
    sub_dct = dct.pop(sub_dct_key_name) or {}
    for k, v in sub_dct.items():
        dct[f"{prefix}{k}"] = v
    return dct


def unflatten(dct, sub_dct_key_name, prefix=None):
    prefix = prefix or f"{sub_dct_key_name}."
    new_dct = {sub_dct_key_name: {}}
    for k, v in dct.items():
        if k.startswith(prefix):
            new_k = k[len(prefix) :]
            new_dct[sub_dct_key_name][new_k] = v
        else:
            new_dct[k] = v
    return new_dct


def unzip_file(file_path, dest_dir):
    """
    Unzip the data given the input and output path.

    Args:
        file_path (str): The path of the ZIP file to be extracted.
        dest_dir (str): The destination directory where the contents will be extracted.

    Returns:
        None
    """
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(dest_dir)


# Taken from https://github.com/langchain-ai/langchain/blob/987099cfcda6f20140228926e9d39eed5ccd35b4/libs/core/langchain_core/runnables/config.py#L528
async def run_in_executor(
    executor: Optional[Executor],
    func: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """Run a function in an executor.

    Args:
        executor (Executor): The executor.
        func (Callable[P, Output]): The function.
        *args (Any): The positional arguments to the function.
        **kwargs (Any): The keyword arguments to the function.

    Returns:
        Output: The output of the function.
    """

    def wrapper() -> T:
        try:
            return func(*args, **kwargs)
        except StopIteration as exc:
            # StopIteration can't be set on an asyncio.Future
            # it raises a TypeError and leaves the Future pending forever
            # so we need to convert it to a RuntimeError
            raise RuntimeError from exc

    # TODO (chiragjn): When running under starlette context, it would be better if we use the pool managed
    #   by starlette
    #   from starlette.concurrency import run_in_threadpool
    #   run_in_threadpool(wrapper)
    if executor is None:
        # Use default executor with context copied from current context
        return await asyncio.get_running_loop().run_in_executor(
            None,
            cast(Callable[..., T], partial(copy_context().run, wrapper)),
        )

    return await asyncio.get_running_loop().run_in_executor(executor, wrapper)
