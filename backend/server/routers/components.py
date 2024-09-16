from fastapi import APIRouter, Depends

from backend.modules.dataloaders.loader import list_dataloaders
from backend.modules.parsers.parser import list_parsers
from backend.modules.query_controllers.query_controller import list_query_controllers

router = APIRouter(prefix="/v1/components", tags=["components"])


@router.get("/parsers")
def get_parsers():
    """Get available parsers from the registered parsers"""
    parsers = list_parsers()
    return parsers


@router.get("/dataloaders")
def get_dataloaders():
    """Get available data loaders from registered data loaders"""
    data_loaders = list_dataloaders()
    return data_loaders


@router.get("/query_controllers")
def get_query_controllers():
    """Get available query controllers from registered query controllers"""
    query_controllers = list_query_controllers()
    return query_controllers
