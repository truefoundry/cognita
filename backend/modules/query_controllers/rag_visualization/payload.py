"""
Sample payloads for RAG Visualization API
"""

RAG_VISUALIZATION_BASIC_PAYLOAD = {
    "collection_name": "sample-collection",
    "query": "What are the key features of the product?",
    "model_configuration": {
        "name": "openai/gpt-3.5-turbo",
        "type": "chat",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context}\nQuestion: {question}",
    "retriever_name": "vectorstore",
    "retriever_config": {
        "search_type": "similarity",
        "search_kwargs": {"k": 5},
        "filter": {},
    },
    "include_embeddings": False,
    "include_intermediate_steps": True,
    "include_timing_info": True,
    "internet_search_enabled": False,
    "stream": False,
}

RAG_VISUALIZATION_WITH_RERANKING_PAYLOAD = {
    "collection_name": "sample-collection",
    "query": "Explain the technical specifications and requirements",
    "model_configuration": {
        "name": "openai/gpt-4",
        "type": "chat",
        "parameters": {"temperature": 0.2, "max_tokens": 2048},
    },
    "prompt_template": "Based on the provided context, give a comprehensive answer to the question:\nContext: {context}\nQuestion: {question}",
    "retriever_name": "contextual-compression",
    "retriever_config": {
        "search_type": "similarity",
        "search_kwargs": {"k": 10},
        "compressor_model_name": "mixedbread-ai/mxbai-rerank-large-v1",
        "top_k": 5,
        "filter": {},
    },
    "include_embeddings": True,
    "include_intermediate_steps": True,
    "include_timing_info": True,
    "internet_search_enabled": False,
    "stream": False,
}

RAG_VISUALIZATION_STREAMING_PAYLOAD = {
    "collection_name": "sample-collection",
    "query": "What are the main benefits and use cases?",
    "model_configuration": {
        "name": "openai/gpt-3.5-turbo",
        "type": "chat",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": "Answer the question based on the context provided:\nContext: {context}\nQuestion: {question}",
    "retriever_name": "multi-query",
    "retriever_config": {
        "search_type": "similarity",
        "search_kwargs": {"k": 8},
        "retriever_llm_configuration": {
            "name": "openai/gpt-3.5-turbo",
            "type": "chat",
            "parameters": {"temperature": 0.0},
        },
        "filter": {},
    },
    "include_embeddings": False,
    "include_intermediate_steps": True,
    "include_timing_info": True,
    "internet_search_enabled": True,
    "stream": True,
}
