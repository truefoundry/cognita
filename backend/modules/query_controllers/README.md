## Query Controller

Code responsible for implementing the Query interface of RAG application. We expose `BaseQueryControler` class that comes with pre-definded methods for getting `_get_vector_store`, `_get_llm` and we also expose `DefaultQueryController` controller where we have given example of how a basic retreival query can be implemented. The methods defined in these query controllers are added routes to your FastAPI server.

### Steps to add your custom Query Controller

- Add your Query controller class in `backend/modules/query_controllers/`

- Add `query_controller` decorator to your class and pass the name of your custom controller as argument

```sample.py
from backend.modules.query_controllers.base import BaseQueryController
from backend.utils.decorator import query_controller

@query_controller("/my-controller")
class MyCustomController(BaseQueryController):
    ...
```

- Add methods to this controller as per your needs and use our http decorators like `post, get, delete` to make your methods an API

```sample.py
from backend.utils.decorator import post

@query_controller("/my-controller")
class MyCustomController(BaseQueryController):
    ...

    @post("/answer")
    def answer(query: str):
        # Write code to express your logic for answer
        # This API will be exposed as POST /my-controller/answer
        ...
```

- Import your custom controller class at `backend/modules/query_controllers/__init__.py`

```__init__.py
...
from backend.modules.query_controllers.sample import MyCustomController
```