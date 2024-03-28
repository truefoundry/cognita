QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY = {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "vectorstore",
    "retriever_config": {
        "search_type": "similarity",
        "search_kwargs": {
            "k": 20
        }
    },
    "stream": False
}

QUERY_WITH_VECTOR_STORE_RETRIEVER_PAYLOAD = {
    "summary": "vector store retriever with similarity search",
    "description": """
        Payload for answering the question using the vector store retriever. 
        LLM provider can be changed to ollama/truefoundry/openai.
        search_type can either be similarity or mmr or similarity_score_threshold.""",
    "value": QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY,
}
#######

QUERY_WITH_VECTOR_STORE_RETRIEVER_MMR = {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "vectorstore",
    "retriever_config": {
        "search_type": "mmr",
        "search_kwargs": {
            "k": 20,
            "fetch_k": 30,
        }
    },
    "stream": False
}

QUERY_WITH_VECTOR_STORE_RETRIEVER_MMR_PAYLOAD = {
    "summary": "vector store retriever with mmr",
    "description": """
        Payload for answering the question using the vector store retriever with search type mmr. 
        Requires k and fetch_k in search_kwargs. mmr support depends on vector db. 
        search_type can either be similarity or mmr or similarity_score_threshold.
        LLM provider can be changed to ollama/truefoundry/openai""",
    "value": QUERY_WITH_VECTOR_STORE_RETRIEVER_MMR,
}
#######

QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY_SCORE = {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "vectorstore",
    "retriever_config": {
        "search_type": "similarity_score_threshold",
        "search_kwargs": {
            "score_threshold": 0.7
        }
    },
    "stream": False
}

QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY_SCORE_PAYLOAD = {
    "summary": "vector store retriever with threshold score",
    "description": """
        Payload for answering the question using the vector store retriever with search type similarity_score_threshold. 
        Requires score_threshold float (0~1) in search kwargs. 
        search_type can either be similarity or mmr or similarity_score_threshold.
        LLM provider can be changed to ollama/truefoundry/openai""",
    "value": QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY_SCORE,
}
#######

QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER =  {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "contexual-compression",
    "retriever_config": {
        "compressor_model_provider" : "mixbread-ai",
        "compressor_model_name" : "mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 5,
        "search_type": "similarity",
        "search_kwargs": {
            "k": 20
        }
    },
    "stream": False
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD = {
    "summary": "contextual compression (re-ranker) retriever with similariy search",
    "description": """
        Payload for answering the question using the contexual compression retriever. 
        search_type can either be similarity or mmr or similarity_score_threshold.
        LLM provider can be changed to ollama/truefoundry/openai. 
        Currently only support for mixedbread-ai/mxbai-rerank-xsmall-v1 reranker is added. 
        You can add more rerankers in the code and use here.""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER,
}
#####


QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_MMR =  {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "contexual-compression",
    "retriever_config": {
        "compressor_model_provider" : "mixbread-ai",
        "compressor_model_name" : "mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 7,
        "search_type": "mmr",
        "search_kwargs": {
            "k": 20,
            "fetch_k": 30,
        }
    },
    "stream": False
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_MMR_PAYLOAD = {
    "summary": "contextual compression (re-ranker) retriever with mmr",
    "description": """
        Payload for answering the question using the contexual compression retriever with search type mmr. 
        search_type can either be similarity or mmr or similarity_score_threshold.
        Requires k and fetch_k in search kwargs.  mmr support depends on vector db. 
        LLM provider can be changed to ollama/truefoundry/openai. 
        Currently only support for mixedbread-ai/mxbai-rerank-xsmall-v1 reranker is added. 
        You can add more rerankers in the code and use here.""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_MMR,
}

#####


QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE =  {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "contexual-compression",
    "retriever_config": {
        "compressor_model_provider" : "mixbread-ai",
        "compressor_model_name" : "mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 5,
        "search_type": "similarity_score_threshold",
        "search_kwargs": {
            "score_threshold": 0.7
        }
    },
    "stream": False
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE_PAYLOAD = {
    "summary": "contextual compression (re-ranker) retriever with threshold score",
    "description": """
        Payload for answering the question using the contexual compression retriever with search type similarity_score_threshold. 
        search_type can either be similarity or mmr or similarity_score_threshold.
        Requires score_threshold float (0~1) in search kwargs. LLM provider can be changed to ollama/truefoundry/openai. 
        Currently only support for mixedbread-ai/mxbai-rerank-xsmall-v1 reranker is added. You can add more rerankers in the code and use here.""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE,
}

#####

QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY = {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "multi-query",
    "retriever_config": {
        "search_type": "similarity",
        "search_kwargs": {
            "k": 20
        },
        "retriever_llm_configuration": {
            "name": "openai-devtest/gpt-3-5-turbo",
            "provider": "truefoundry",
            "parameters": {
                "temperature": 0.9
            }
        },
    },
    "stream": False
}

QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD = {
    "summary": "multi-query retriever with similarity search",
    "description": """
        Typically used for complex user queries.
        Payload for answering the question using the multi-query retriever. 
        search_type can either be similarity or mmr or similarity_score_threshold.
        LLM provider for both model_configuration and retriever_llm_configuration can be changed to ollama/truefoundry/openai""",
    "value": QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY,
}
#######


QUERY_WITH_MULTI_QUERY_RETRIEVER_MMR = {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "multi-query",
    "retriever_config": {
        "search_type": "mmr",
        "search_kwargs": {
            "k": 20,
            "fetch_k": 30,
        },
        "retriever_llm_configuration": {
            "name": "openai-devtest/gpt-3-5-turbo",
            "provider": "truefoundry",
            "parameters": {
                "temperature": 0.9
            }
        },
    },
    "stream": False
}

QUERY_WITH_MULTI_QUERY_RETRIEVER_MMR_PAYLOAD = {
    "summary": "multi-query retriever with mmr",
    "description": """
        Typically used for complex user queries.
        Payload for answering the question using the vector store retriever with search type mmr. 
        search_type can either be similarity or mmr or similarity_score_threshold.
        Requires k and fetch_k in search_kwargs. mmr support depends on vector db. 
        LLM provider for both model_configuration and retriever_llm_configuration can be changed to ollama/truefoundry/openai""",
    "value": QUERY_WITH_MULTI_QUERY_RETRIEVER_MMR,
}
#######

QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE = {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "multi-query",
    "retriever_config": {
        "search_type": "similarity_score_threshold",
        "search_kwargs": {
            "score_threshold": 0.7
        },
        "retriever_llm_configuration": {
            "name": "openai-devtest/gpt-3-5-turbo",
            "provider": "truefoundry",
            "parameters": {
                "temperature": 0.9
            }
        },
    },
    "stream": False
}

QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE_PAYLOAD = {
    "summary": "multi-query retriever with similarity score threshold",
    "description": """
        Typically used for complex user queries.
        Payload for answering the question using the vector store retriever with search type similarity_score_threshold.
        search_type can either be similarity or mmr or similarity_score_threshold.
        Requires score_threshold float (0~1) in search kwargs. 
        LLM provider for both model_configuration and retriever_llm_configuration can be changed to ollama/truefoundry/openai""",
    "value": QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE,
}
#######


QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_MMR = {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "contexual-compression-multi-query",
    "retriever_config": {
        "compressor_model_provider" : "mixbread-ai",
        "compressor_model_name" : "mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 7,
        "search_type": "mmr",
        "search_kwargs": {
            "k": 20,
            "fetch_k": 30,
        },
        "retriever_llm_configuration": {
            "name": "openai-devtest/gpt-3-5-turbo",
            "provider": "truefoundry",
            "parameters": {
                "temperature": 0.9
            }
        },
    },
    "stream": False
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_MMR_PAYLOAD = {
    "summary": "multi-query reranker retriever with mmr",
    "description": """
        Typically used for complex user queries.
        Payload for answering the question using the multi-query reranker retriever with search type mmr.
        search_type can either be similarity or mmr or similarity_score_threshold.
        Requires k and fetch_k in search_kwargs. mmr support depends on vector db. 
        LLM provider for both model_configuration and retriever_llm_configuration can be changed to ollama/truefoundry/openai""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_MMR,
}
#######

QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY = {
    "collection_name": "testcollection",
    "query": "What are the features of Diners club black metal edition?",
    "model_configuration": {
        "name": "openai-devtest/gpt-3-5-turbo",
        "provider": "truefoundry",
        "parameters": {
            "temperature": 0.1
        }
    },
    "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
    "retriever_name": "contexual-compression-multi-query",
    "retriever_config": {
        "compressor_model_provider" : "mixbread-ai",
        "compressor_model_name" : "mixedbread-ai/mxbai-rerank-xsmall-v1",
        "top_k": 5,
        "search_type": "similarity",
        "search_kwargs": {
            "k": 20
        },
        "retriever_llm_configuration": {
            "name": "openai-devtest/gpt-3-5-turbo",
            "provider": "truefoundry",
            "parameters": {
                "temperature": 0.1
            }
        },
    },
    "stream": False
}

QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD = {
    "summary": "multi-query reranker retriever with similarity ",
    "description": """
        Typically used for complex user queries.
        Payload for answering the question using the vector store retriever with search type similarity.
        search_type can either be similarity or mmr or similarity_score_threshold.
        LLM provider for both model_configuration and retriever_llm_configuration can be changed to ollama/truefoundry/openai""",
    "value": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY,
}
#######