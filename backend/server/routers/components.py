from fastapi import APIRouter

from backend.modules.dataloaders.loader import LOADER_REGISTRY
from backend.modules.embedder.embedder import EMBEDDER_REGISTRY
from backend.modules.parsers.parser import PARSER_REGISTRY
from backend.server.decorators import QUERY_CONTROLLER_REGISTRY

router = APIRouter(prefix="/v1/components", tags=["components"])


@router.get("/parsers")
def get_parsers():
    """Get available parsers from the registered parsers"""
    parsers = []
    for key, value in PARSER_REGISTRY.items():
        parsers.append(
            {"name": key, "supported_extensions": value.get("supported_extensions")}
        )
    return parsers


@router.get("/embedders")
def get_embedders():
    """Get available embedders from registered embedders"""
    embedders = []
    for key, _ in EMBEDDER_REGISTRY.items():
        embedders.append({"name": key})
    return embedders


@router.get("/data_loaders")
def get_data_loaders():
    """Get available data loaders from registered data loaders"""
    data_loaders = []
    for key, _ in LOADER_REGISTRY.items():
        data_loaders.append({"name": key})
    return data_loaders


@router.get("/query_controllers")
def get_query_controllers():
    """Get available query controllers from registered query controllers"""
    query_controllers = []
    for key, value in QUERY_CONTROLLER_REGISTRY.items():
        query_controllers.append({"name": key})
    return query_controllers
