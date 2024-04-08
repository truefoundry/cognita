from backend.modules.query_controllers import ExampleQueryController
import asyncio

# Payload for the query
# You can try different payload examples from `backend.modules.query_controllers.example.payload`
request = {
    "collection_name": "creditcard",
    "query": "Explain in detail different categories of credit cards",
    "model_configuration": {
        "name": "openai-main/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {"temperature": 0.1},
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "contexual-compression-multi-query",
    "retriever_config": {
        "compressor_model_provider": "mixbread-ai",
        "compressor_model_name": "mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 7,
        "search_type": "mmr",
        "search_kwargs": {
            "k": 20,
            "fetch_k": 30,
        },
        "retriever_llm_configuration": {
            "name": "openai-main/gpt-3-5-turbo",
            "provider": "truefoundry",
            "parameters": {"temperature": 0.9},
        },
    },
    "stream": False,
}
# You can change the query here
print(f"Payload: {request}")

# Create a controller object
controller = ExampleQueryController()

# Get the answer
answer = asyncio.run(controller.answer(request))
print(f"Answer: {answer}")
