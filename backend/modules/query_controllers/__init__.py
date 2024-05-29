from backend.modules.query_controllers.example.controller import ExampleQueryController
from backend.modules.query_controllers.multimodal.controller import (
    MultiModalQueryController,
)
from backend.modules.query_controllers.query_controller import register_query_controller

register_query_controller("default", ExampleQueryController)
register_query_controller("multimodal", MultiModalQueryController)
