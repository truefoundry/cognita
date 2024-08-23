
# Cognita Repository

This repository is specifically configured for N-iX. Below are the instructions to set up and run the services, as well as to configure Azure and Amazon Bedrock models.

## Running the Service

To start all necessary services, use the following command:

```bash
docker compose --env-file compose.env --profile '*' up -d --build
```

This will spin up all required services. To stop the services, use:

```bash
docker compose --env-file compose.env --profile '*' down
```

## Setting Up Azure Credentials

To configure Azure credentials, uncomment the Azure section in the `model_config.sample.yaml` file. After making the changes, copy it to `models_config.yaml` or specify the changes directly in `models_config.yaml`.

Here is the Azure configuration block:

```yaml
########################### AzureOpenAI ###########################################
#   Uncomment this provider if you want to use OpenAI as a models provider    #
#   Remember to set `OPENAI_API_KEY` in container environment                 #
##############################################################################

  - provider_name: azure
    api_format: openai
    api_key_env_var: AZURE_OPENAI_API_KEY
    embeddings_base_url: 
    llm_base_url: 
    openai_api_version: 
    llm_deployment:
    llm_model_ids:
      - "gpt-4o"
    embedding_deployment: 
    embedding_model_ids:
      - "text-embedding-ada-002"
    reranking_model_ids: []
    default_headers: {} 
```

## Setting Up Bedrock's Model Access

To configure Bedrock's model access, uncomment the Bedrock section in the `model_config.sample.yaml` file:

```yaml
############################ Amazon Bedrock ###########################################
#   Uncomment this provider if you want to use Amazon Bedrock's Claude Sonnet 3.5 as a models provider    #
#   Remember to set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION="us-east-1"` in container environment                 #
###############################################################################

  - provider_name: bedrock
    api_format: amazon
    api_key_env_var: AWS_ACCESS_KEY_ID
    secret_access_key_env_var: AWS_SECRET_ACCESS_KEY
    sesssion_token_env_var: AWS_SESSION_TOKEN
    default_region_env_var: AWS_DEFAULT_REGION
    llm_model_ids:
      - "anthropic.claude-3-5-sonnet-20240620-v1:0"
    embedding_model_ids:
      - "cohere.embed-english-v3"
    reranking_model_ids: []
    default_headers: {}  
```

## Setting Up Environment Variables 

Do not forget to fill in all of the environment variables in `compose.env` file. 