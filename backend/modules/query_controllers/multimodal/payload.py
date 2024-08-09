PROMPT = "You are an AI assistant specialising in information retrieval. Answer the following question precisely by extracting the relavant information given in the images.\nQuestion: {question}"
QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "vectorstore",
    "retriever_config": {"search_type": "similarity", "search_kwargs": {"k": 5}},
    "stream": False,
}

QUERY_WITH_VECTOR_STORE_RETRIEVER_PAYLOAD = {
    "summary": "search with similarity",
    "description": """
        Requires k in search_kwargs for similarity search.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY,
}
#######

QUERY_WITH_VECTOR_STORE_RETRIEVER_MMR = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "vectorstore",
    "retriever_config": {
        "search_type": "mmr",
        "search_kwargs": {
            "k": 5,
            "fetch_k": 7,
        },
    },
    "stream": False,
}

QUERY_WITH_VECTOR_STORE_RETRIEVER_MMR_PAYLOAD = {
    "summary": "search with mmr",
    "description": """
        Requires k and fetch_k in search_kwargs for mmr support depends on vector db.
        search_type can either be similarity or mmr or similarity_score_threshold""",
    "value": QUERY_WITH_VECTOR_STORE_RETRIEVER_MMR,
}
#######

QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY_SCORE = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "vectorstore",
    "retriever_config": {
        "search_type": "similarity_score_threshold",
        "search_kwargs": {"score_threshold": 0.7},
    },
    "stream": False,
}

QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY_SCORE_PAYLOAD = {
    "summary": "search with threshold score",
    "description": """
        Requires score_threshold float (0~1) in search kwargs.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY_SCORE,
}
#######

QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "contextual-compression",
    "retriever_config": {
        "compressor_model_name": "local-infinity/mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 5,
        "search_type": "similarity",
        "search_kwargs": {"k": 10},
    },
    "stream": False,
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD = {
    "summary": "similarity search + re-ranking",
    "description": """
        Requires k in search_kwargs for similarity search.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER,
}
#####


QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_MMR = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "contextual-compression",
    "retriever_config": {
        "compressor_model_name": "local-infinity/mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 5,
        "search_type": "mmr",
        "search_kwargs": {
            "k": 10,
            "fetch_k": 30,
        },
    },
    "stream": False,
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_MMR_PAYLOAD = {
    "summary": "mmr + re-ranking",
    "description": """
        Requires k and fetch_k in search kwargs for mmr.
        search_type can either be similarity or mmr or similarity_score_threshold.
        Currently only support for mixedbread-ai/mxbai-rerank-xsmall-v1 reranker is added.""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_MMR,
}

#####


QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "contextual-compression",
    "retriever_config": {
        "compressor_model_name": "local-infinity/mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 5,
        "search_type": "similarity_score_threshold",
        "search_kwargs": {"score_threshold": 0.7},
    },
    "stream": False,
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE_PAYLOAD = {
    "summary": "threshold score + re-ranking",
    "description": """
        Requires score_threshold float (0~1) in search kwargs for similarity search.
        search_type can either be similarity or mmr or similarity_score_threshold.
        Currently only support for mixedbread-ai/mxbai-rerank-xsmall-v1 reranker is added""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE,
}

#####

QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "multi-query",
    "retriever_config": {
        "search_type": "similarity",
        "search_kwargs": {"k": 5},
        "retriever_llm_configuration": {
            "name": "truefoundry/openai-main/gpt-3-5-turbo",
            "parameters": {"temperature": 0.9},
        },
    },
    "stream": False,
}

QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD = {
    "summary": "multi-query + similarity search",
    "description": """
        Typically used for complex user queries.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY,
}
#######


QUERY_WITH_MULTI_QUERY_RETRIEVER_MMR = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "multi-query",
    "retriever_config": {
        "search_type": "mmr",
        "search_kwargs": {
            "k": 5,
            "fetch_k": 10,
        },
        "retriever_llm_configuration": {
            "name": "truefoundry/openai-main/gpt-3-5-turbo",
            "parameters": {"temperature": 0.9},
        },
    },
    "stream": False,
}

QUERY_WITH_MULTI_QUERY_RETRIEVER_MMR_PAYLOAD = {
    "summary": "multi-query + mmr",
    "description": """
        Requires k and fetch_k in search_kwargs for mmr.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_MULTI_QUERY_RETRIEVER_MMR,
}
#######

QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-3-5-turbo",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "multi-query",
    "retriever_config": {
        "search_type": "similarity_score_threshold",
        "search_kwargs": {"score_threshold": 0.7},
        "retriever_llm_configuration": {
            "name": "truefoundry/openai-main/gpt-4o-mini",
            "parameters": {"temperature": 0.9},
        },
    },
    "stream": False,
}

QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE_PAYLOAD = {
    "summary": "multi-query + threshold score",
    "description": """
        Typically used for complex user queries.
        Requires score_threshold float (0~1) in search kwargs.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE,
}
#######


QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_MMR = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "contextual-compression-multi-query",
    "retriever_config": {
        "compressor_model_name": "local-infinity/mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 5,
        "search_type": "mmr",
        "search_kwargs": {
            "k": 10,
            "fetch_k": 30,
        },
        "retriever_llm_configuration": {
            "name": "truefoundry/openai-main/gpt-3-5-turbo",
            "parameters": {"temperature": 0.9},
        },
    },
    "stream": False,
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_MMR_PAYLOAD = {
    "summary": "multi-query + re-ranking +  mmr",
    "description": """
        Typically used for complex user queries.
        Requires k and fetch_k in search_kwargs for mmr.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_MMR,
}
#######

QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "contextual-compression-multi-query",
    "retriever_config": {
        "compressor_model_name": "local-infinity/mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 5,
        "search_type": "similarity",
        "search_kwargs": {"k": 10},
        "retriever_llm_configuration": {
            "name": "truefoundry/openai-main/gpt-3-5-turbo",
            "parameters": {"temperature": 0.1, "max_tokens": 1024},
        },
    },
    "stream": False,
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD = {
    "summary": "multi-query + re-ranking + similarity ",
    "description": """
        Typically used for complex user queries.
        Requires k in search_kwargs for similarity search.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY,
}
#######

QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE = {
    "collection_name": "finance",
    "query": "Explain key operating metrics of FY20",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini",
        "parameters": {"temperature": 0.1, "max_tokens": 1024},
    },
    "prompt_template": PROMPT,
    "retriever_name": "contextual-compression-multi-query",
    "retriever_config": {
        "compressor_model_name": "local-infinity/mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 5,
        "search_type": "similarity_score_threshold",
        "search_kwargs": {"score_threshold": 0.7},
        "retriever_llm_configuration": {
            "name": "truefoundry/openai-main/gpt-3-5-turbo",
            "parameters": {"temperature": 0.1, "max_tokens": 1024},
        },
    },
    "stream": False,
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE_PAYLOAD = {
    "summary": "multi-query + re-ranking + threshold score",
    "description": """
        Typically used for complex user queries.
        Requires k in search_kwargs for similarity search.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE,
}
#######
