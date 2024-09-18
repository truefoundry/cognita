import logging
from truefoundry.deploy import (
    HttpProbe,
    OCIRepo,
    Job,
    NodeSelector,
    Param,
    Resources,
    StringDataMount,
    Kustomize,
    Image,
    HelmRepo,
    ApplicationSet,
    Service,
    Manual,
    Build,
    Helm,
    DockerFileBuild,
    GitSource,
    HealthProbe,
    Port,
    LocalSource,
)
import argparse
from deployment.config import *

logging.basicConfig(level=logging.INFO)

def run_deploy(workspace_fqn, application_set_name,ml_repo,base_domain_url):
    workspace = workspace_fqn.split(":")[1]
    QDRANT_URL = f"http://{VECTOR_DB_HELM_NAME}.{workspace}.svc.cluster.local:6333"
    application_set = ApplicationSet(
        name=application_set_name,
        components=[
            Service(
                    name=BACKEND_SERVICE_NAME,
                    image=Build(
                        # Set build_source=LocalSource(local_build=False), in order to deploy code from your local.
                        # With local_build=False flag, docker image will be built on cloud instead of local
                        # Else it will try to use docker installed on your local machine to build the image
                        build_source=LocalSource(local_build=False),
                        build_spec=DockerFileBuild(
                            dockerfile_path="./backend/Dockerfile",
                            build_context_path="./",
                            command='/bin/bash -c "set -e; prisma db push --schema ./backend/database/schema.prisma && uvicorn --host 0.0.0.0 --port 8000 backend.server.app:app"',
                        ),
                    ),
                    resources=Resources(
                        cpu_request=0.5,
                        cpu_limit=1.0,
                        memory_request=500,
                        memory_limit=1000,
                        ephemeral_storage_request=1000,
                        ephemeral_storage_limit=2000,
                        node=NodeSelector(capacity_type="spot_fallback_on_demand"),
                    ),
                env={
                    "JOB_FQN": f"{workspace_fqn}:{INDEXER_SERVICE_NAME}",
                    "LOG_LEVEL": "DEBUG",
                    "DATABASE_URL": f"postgresql://admin:password@{DATABASE_NAME}-postgresql.{workspace}.svc.cluster.local:5432/cognita-config",
                    "INFINITY_URL": f"http://{INFINITY_SERVICE_NAME}.{workspace}.svc.cluster.local:8000",
                    "ML_REPO_NAME": ml_repo,
                    "BRAVE_API_KEY": "tfy-secret://internal:cognita:BRAVE_API_KEY",
                    "INFINITY_API_KEY": "tfy-secret://internal:cognita:INFINITY_API_KEY",
                    "VECTOR_DB_CONFIG": str({"provider":"qdrant","url":QDRANT_URL,"api_key":""}),
                    "CARBON_AI_API_KEY": "tfy-secret://internal:cognita:CARBON_AI_API_KEY",
                    "JOB_COMPONENT_NAME": f"{workspace}-{INDEXER_SERVICE_NAME}",
                    "MODELS_CONFIG_PATH": "./models_config.truefoundry.yaml",
                    "UNSTRUCTURED_IO_URL": f"http://{UNSTRUCTURED_IO_SERVICE_NAME}.{workspace}.svc.cluster.local:8000",
                    "METADATA_STORE_CONFIG": '{"provider":"prisma"}',
                    "UNSTRUCTURED_IO_API_KEY": "tfy-secret://internal:cognita:UNSTRUCTURED_IO_API_KEY",
                },
                ports=[
                    Port(
                        port=8000,
                        protocol="TCP",
                        expose=True,
                        app_protocol="http",
                        host=f"{application_set_name}.{base_domain_url}",
                        path="/api/",
                    )
                ],
                mounts=[
                    StringDataMount(
                        mount_path="/models_config.truefoundry.yaml",
                        data=f'''
                                model_providers:
                                - provider_name: truefoundry
                                    api_format: openai
                                    base_url: https://llm-gateway.truefoundry.com/api/inference/openai
                                    api_key_env_var: TFY_API_KEY
                                    llm_model_ids:
                                    - "openai-main/gpt-4o-mini"
                                    - "openai-main/gpt-4-turbo"
                                    - "openai-main/gpt-3-5-turbo"
                                    - "azure-openai/gpt-4"
                                    - "together-ai/llama-3-70b-chat-hf"
                                    embedding_model_ids:
                                    - "openai-main/text-embedding-ada-002"
                                    reranking_model_ids: []
                                    default_headers:
                                    "X-TFY-METADATA": '{{"tfy_log_request": "true", "Custom-Metadata": "Cognita-LLM-Request"}}'

                                - provider_name: local-infinity
                                    api_format: openai
                                    base_url: http://{INFINITY_SERVICE_NAME}.{workspace}.svc.cluster.local:8000
                                    api_key_env_var: INFINITY_API_KEY
                                    llm_model_ids: []
                                    embedding_model_ids:
                                    - "mixedbread-ai/mxbai-embed-large-v1"
                                    reranking_model_ids:
                                    - "mixedbread-ai/mxbai-rerank-xsmall-v1"
                                    default_headers: {{}}
                            '''
                    )
                ],
                    liveness_probe=HealthProbe(
                    config=HttpProbe(path="/health-check", port=8000, scheme="HTTP"),
                    initial_delay_seconds=10,
                    period_seconds=60,
                    timeout_seconds=2,
                    success_threshold=1,
                    failure_threshold=5,
                ),
                readiness_probe=HealthProbe(
                    config=HttpProbe(path="/health-check", port=8000, scheme="HTTP"),
                    initial_delay_seconds=10,
                    period_seconds=60,
                    timeout_seconds=2,
                    success_threshold=1,
                    failure_threshold=5,
                ),
                replicas=1.0,
                allow_interception=False,
            )
        ],
        workspace_fqn=workspace_fqn,
        )

    application_set.deploy(workspace_fqn=workspace_fqn,wait=False)




if __name__ == "__main__":
    
    # Setup the argument parser by instantiating `ArgumentParser` class
    parser = argparse.ArgumentParser()
    # Add the parameters as arguments
    parser.add_argument(
        '--workspace_fqn', 
        type=str,
        required=True, 
        help='The workspace FQN where the application set will be deployed'
    )
    parser.add_argument(
        '--application_set_name',
        type=str, 
        help='Name of the application set'
    )
    parser.add_argument(
        "--ml_repo",
        type=str,
        required=True,
        help="""\
            The name of the ML Repo to track metrics and models.
            You can create one from the ML Repos Tab on the UI.
            Docs: https://docs.truefoundry.com/docs/key-concepts#creating-an-ml-repo,
        """
    ) 
    parser.add_argument(
        "--base_domain_url",
        type=str,
        required=True,
        help="""\
            The host name of the application set.
        """
    ) 
    
    args = parser.parse_args()

    run_deploy(**vars(args))
    


