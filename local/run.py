from backend.modules.query_controllers.default.types import DEFAULT_QUERY, DefaultQueryInput
from backend.modules.query_controllers import DefaultQueryController
import asyncio

# You can change the query here
print(f"Default Query: {DEFAULT_QUERY}")

# Create a request object
request = DefaultQueryInput(**DEFAULT_QUERY)

# Create a controller object
controller = DefaultQueryController()

# Get the answer
answer = asyncio.run(controller.answer(request))
print(f"Answer: {answer}")