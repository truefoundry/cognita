QUERY_CONTROLLER_REGISTRY = {}


def register_query_controller(name: str, cls):
    """
    Registers all the available query controllers
    """
    global QUERY_CONTROLLER_REGISTRY
    if name in QUERY_CONTROLLER_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__} already taken by {QUERY_CONTROLLER_REGISTRY[name].__name__}"
        )
    QUERY_CONTROLLER_REGISTRY[name] = cls


def list_query_controllers():
    """
    Returns a list of all the registered query controllers.

    Returns:
        List[Dict]: A list of all the registered query controllers.
    """
    global QUERY_CONTROLLER_REGISTRY
    return [
        {
            "type": type,
            "class": cls.__name__,
        }
        for type, cls in QUERY_CONTROLLER_REGISTRY.items()
    ]
