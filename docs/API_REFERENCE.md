# API Reference Document

This file documents the associated APIs that are used in RAG application.

---

If you run the server locally using the command: `uvicorn --host 0.0.0.0 --port 8080 backend.server.app:app --reload`
Then, Swagger doc will be available at: `http://localhost:8080/`

### Components

This group of API list down different components of RAG that are registered.

---

-   GET `/v1/components/parsers`: Returns a list of available parsers.

    ```curl
    curl -X 'GET' \
    'http://localhost:8080/v1/components/parsers' \
    -H 'accept: application/json'
    ```

    Current available parsers include: `MarkdownParser`, `PdfParserUsingPyMuPDF`, `TextParser`.

-   GET `/v1/components/embedders`: Returns a list of available embedders.

    ```curl
    curl -X 'GET' \
    'http://localhost:8080/v1/components/embedders' \
    -H 'accept: application/json'
    ```

    Current available `default` embeddings include: `TrueFoundryEmbeddings`

-   `/v1/components/dataloaders`: Returns a list of available data loaders.
    ```curl
    curl -X 'GET' \
    'http://localhost:8080/v1/components/dataloaders' \
    -H 'accept: application/json'
    ```
    Current available dataloaders are: `github`, `local`, `web`, `mlfoundry`, `artifact`.

### Data Sources

This API is used for creating/listing a new data source. Data source is one through which data is scanned and loaded for indexing.

---

-   GET `/v1/data_source/`: Returns a list of available data sources.

    ```curl
    curl -X 'GET' \
    'http://localhost:8080/v1/data_source/' \
    -H 'accept: application/json'
    ```

-   POST `/v1/data_source/`: Creates a new data source.

    -   Creation API requires following fields:
        ```json
        {
            "type": "string",
            "uri": "string",
            "metadata": {}
        }
        ```
    -   Attributes:

        -   `type` (str): The type of the data source. This field is required. One of `mlfoundry` or `local`.
        -   `uri` (str): A unique identifier for the data source. This field is required. This can be FQN of MLRepo or FQN of Artifact with version number from Truefoundry or local folder path.
        -   `metadata` (Optional[Dict[str, Any]]): Any additional configuration for the data source. This field is optional.

        This API returns a `unique data source fqn` that is then used to associate it with the collection.

### Collection

This API is used for managing the collections. Each collection has embedder configuration and associated data sources that forms a key characterisitc of the collection.

---

-   GET `/v1/collections/`: Returns a list of available collections.

    ```curl
      curl -X 'GET' \
      'http://localhost:8080/v1/collections/' \
      -H 'accept: application/json'
    ```

    -   Sample Response:

        ```json
        {
            "collections": [
                {
                    // name of the collection
                    "name": "ps01",

                    // description of the collection
                    "description": "test collection for open src repo",

                    // embedder configuration used to index the data into the collection
                    "embedder_config": {
                        // provider - default, if you init your own embedder add that as provider
                        "provider": "default",
                        "config": {
                            // embedder model name
                            "model": "openai-devtest/text-embedding-ada-002"
                        }
                    },
                    "associated_data_sources": {
                        // currently one associated data source in this collection th' mlfoundry data dir
                        "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp": {
                            // fqn of that data src
                            "data_source_fqn": "mlfoundry::data-dir:truefoundry/prathamesh/reindexing-exp",
                            // parser configuration
                            "parser_config": {
                                "chunk_size": 500,
                                "chunk_overlap": 0,
                                "parser_map": {
                                    ".pdf": "PdfParserFast",
                                    ".txt": "TextParser",
                                    ".md": "MarkdownParser"
                                }
                            },
                            // data src config similar to POST /v1/data_source
                            "data_source": {
                                "type": "mlfoundry",
                                "uri": "data-dir:truefoundry/prathamesh/reindexing-exp",
                                "metadata": null,
                                "fqn": "mlfoundry::data-dir:truefoundry/prathamesh/reindexing-exp"
                            }
                        }
                    }
                }
            ]
        }
        ```

-   POST `/v1/collections/`: Creates a new collection.
    -   This API creates a collection, it requires payload of the form:
        -   ```json
            {
                "name": "collectionName",
                "description": "string",
                "embedder_config": {
                    "provider": "string",
                    "config": {}
                },
                "associated_data_sources": [
                    {
                        "data_source_fqn": "string",
                        "parser_config": {
                            "chunk_size": 500,
                            "chunk_overlap": 0,
                            "parser_map": {
                                ".md": "MarkdownParser",
                                ".pdf": "PdfParserFast",
                                ".txt": "TextParser"
                            }
                        }
                    }
                ]
            }
            ```
-   POST `/v1/collections/{collection_name}`: Deletes an already exisiting collection.
    ```curl
    curl -X 'DELETE' \
      'http://localhost:8080/v1/collections/xyz' \
      -H 'accept: application/json'
    ```

### Retrievers

Any registered question answer API is showcased here. To add your own retriever refer: `backend/modules/query_controllers/README.md`

---

-   POST `/retrievers/answer`: Sample answer method to answer the question using the context from the collection.

    -   It requires the following fields as payload:

        -   `collection_name (str)`: The name of the collection to search in. This is a required field.

        -   `retriever_config (RetrieverConfig)`: The configuration for the retriever that will be used to search the collection. This is a required field and must be an instance of the RetrieverConfig class. `retriever_config` in turn requires following arguments:

            -   `search_type (Literal["mmr", "similarity"])`: "Defines the type of search that the Retriever should perform. Can be "similarity" (default), "mmr", or "similarity_score_threshold".

            -   `k (int)`: The number of results/documents to retrieve. This is a required field and must be a positive integer.

            -   `fetch_k (int)`: Amount of documents to pass to MMR algorithm (Default: 20).

            -   `filter (Optional[dict])`: Optional field to add any filters to query.

        -   `query (str)`: The question that will be searched for in the collection. This is a required field and must be a string with a maximum length of 1000 characters.

        -   `model_configuration (LLMConfig)`: The configuration for the Language Model that will be used to generate the answer to the question using the context. This in turn requires following fields:

            -   `name (str)`: Name of the model from the Truefoundry LLM Gateway
            -   `parameters (dict)`: Any optional parameters of the model like max_tokens, etc

        -   `prompt_template (str)`: The template that will be used to format the context, question, and answer. This is an optional field with a default value. The template must include placeholders for the context and the question.

    -   Example:

        ```curl
        curl -X 'POST' \
          'http://localhost:8080/retrievers/answer' \
          -H 'accept: application/json' \
          -H 'Content-Type: application/json' \
          -d '{
          "collection_name": "ps01",
          "retriever_config": {
            "search_type": "similarity",
            "k": 4,
            "fetch_k": 20,
            "filter": {}
          },
          "query": "What is credit card",
          "model_configuration": {
            "name": "openai-devtest/gpt-3-5-turbo",
            "parameters": {}
          },
          "prompt_template": "Here is the context information:\n\n'\'''\'''\''\n{context}\n'\'''\'''\''\n\nQuestion: {question}\nAnswer:"
        }'
        ```

    -   Response:
        ```json
        {
            "answer": "A credit card is a payment card issued by a financial institution that allows the cardholder to borrow funds to make purchases, with the promise to repay the borrowed amount along with any applicable interest and fees. Credit cards typically have a credit limit, which is the maximum amount that the cardholder can borrow. They are widely used for making purchases, both online and in-person, and often come with benefits such as rewards points, cashback, and other perks.",
            "docs": [
                {
                    "page_content": "# [Freedom card new](https://www.hdfcbank.com/personal/pay/cards/credit-cards/freedom-card-new)\n## Features\n#### Contactless Payment\nContactless Payment\nThe HDFC Bank Freedom Credit Card is enabled for contactless payments, facilitating fast, convenient and secure payments at retail outlets. To see if your Card is contactless, look for the contactless network symbol on your Card.",
                    "metadata": {
                        "Header1": "[Freedom card new](https://www.hdfcbank.com/personal/pay/cards/credit-cards/freedom-card-new)",
                        "Header2": "Features",
                        "Header4": "Contactless Payment",
                        "_document_id": "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp::freedom-card-new.md",
                        "_id": "cb10dd50-695b-4c26-a2be-a73fcb09e2ba",
                        "_collection_name": "ps01"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Freedom card new](https://www.hdfcbank.com/personal/pay/cards/credit-cards/freedom-card-new)\n## Features\n#### Reward Points/Cashback Redemption & Validity\n* CashPoints can also be used for redemption against travel benefits like Flight & Hotel bookings and also on Rewards Catalogue at the SmartBuy Rewards Portal, wherein Credit Card members can redeem up to a maximum of 50% of the booking value through CashPoints at a value of 1 CashPoint = ₹0.15 and the rest of the amount will have to be paid via the Credit Card. To know more on Rewards catalouge, [click here](/personal/pay/cards/credit-cards/simple-rewards-program",
                    "metadata": {
                        "Header1": "[Freedom card new](https://www.hdfcbank.com/personal/pay/cards/credit-cards/freedom-card-new)",
                        "Header2": "Features",
                        "Header4": "Reward Points/Cashback Redemption & Validity",
                        "_document_id": "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp::freedom-card-new.md",
                        "_id": "74d476a3-77f5-46e0-bc69-a49472f20243",
                        "_collection_name": "ps01"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Hdfc bank upi rupay credit card](https://www.hdfcbank.com/personal/pay/cards/credit-cards/hdfc-bank-upi-rupay-credit-card)\n## Features\n#### Revolving Credit\nRevolving Credit\nEnjoy Revolving Credit on your HDFC Bank UPI RuPay Credit Card at nominal interest rate. Please refer to the Fees and Charges section for more details.",
                    "metadata": {
                        "Header1": "[Hdfc bank upi rupay credit card](https://www.hdfcbank.com/personal/pay/cards/credit-cards/hdfc-bank-upi-rupay-credit-card)",
                        "Header2": "Features",
                        "Header4": "Revolving Credit",
                        "_document_id": "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp::hdfc-bank-upi-rupay-credit-card.md",
                        "_id": "30a72a77-5055-48be-b0ba-18adcf06ed5e",
                        "_collection_name": "ps01"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Hdfc bank upi rupay credit card](https://www.hdfcbank.com/personal/pay/cards/credit-cards/hdfc-bank-upi-rupay-credit-card)\n## Features\n#### Reward Point/Cashback Redemption & Validity\n* CashPoints can also be used for redemption against travel benefits like Flight & Hotel bookings and also on Rewards Catalogue at the SmartBuy Rewards Portal, wherein Credit Card members can redeem up to a maximum of 50% of the booking value through CashPoints at a value of 1 CashPoint = ₹0.25 and the rest of the amount will have to be paid via the Credit Card. To know more on Rewards catalouge, [click here](/personal/pay/cards/credit-cards/claim-rewards",
                    "metadata": {
                        "Header1": "[Hdfc bank upi rupay credit card](https://www.hdfcbank.com/personal/pay/cards/credit-cards/hdfc-bank-upi-rupay-credit-card)",
                        "Header2": "Features",
                        "Header4": "Reward Point/Cashback Redemption & Validity",
                        "_document_id": "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp::hdfc-bank-upi-rupay-credit-card.md",
                        "_id": "a544165f-0542-43cc-a38b-154344ae5d16",
                        "_collection_name": "ps01"
                    },
                    "type": "Document"
                }
            ]
        }
        ```
