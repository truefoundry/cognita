from backend.modules.query_controllers.example.controller import ExampleQueryController
from backend.modules.query_controllers.query_controller import register_query_controller
from backend.modules.query_controllers.summary.controller import (
    IntelligentSummaryQueryController,
)

register_query_controller("default", ExampleQueryController)
register_query_controller("summary", IntelligentSummaryQueryController)
