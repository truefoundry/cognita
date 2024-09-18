import argparse
import json
import logging

from truefoundry.deploy import (
    ApplicationSet,
    Build,
    DockerFileBuild,
    GitSource,
    HealthProbe,
    Helm,
    HelmRepo,
    HttpProbe,
    Image,
    Job,
    Kustomize,
    LocalSource,
    Manual,
    NodeSelector,
    OCIRepo,
    Param,
    Port,
    Resources,
    Service,
    StringDataMount,
)

from deployment.config import *

logging.basicConfig(level=logging.INFO)


def run_deploy(
    workspace_fqn: str, application_set_name: str, ml_repo: str, base_domain_url: str
):
    workspace = workspace_fqn.split(":")[1]
    QDRANT_URL = f"http://{VECTOR_DB_HELM_NAME}.{workspace}.svc.cluster.local:6333"
    VECTOR_DB_CONFIG = json.dumps(
        {"provider": "qdrant", "url": QDRANT_URL, "api_key": ""}
    )
    application_set = ApplicationSet(
        name=application_set_name,
        components=[
            Job(
                name=INDEXER_SERVICE_NAME,
                image=Build(
                    build_source=LocalSource(local_build=False),
                    build_spec=DockerFileBuild(
                        dockerfile_path="./backend/Dockerfile",
                        build_context_path="./",
                        command='/bin/bash -c "set -e; prisma generate --schema ./backend/database/schema.prisma && python -m backend.indexer.main  --collection_name {{collection_name}} --data_source_fqn {{data_source_fqn}} --data_ingestion_run_name {{data_ingestion_run_name}} --data_ingestion_mode {{data_ingestion_mode}} --raise_error_on_failure  {{raise_error_on_failure}}"',
                    ),
                ),
                trigger=Manual(type="manual"),
                trigger_on_deploy=False,
                params=[
                    Param(name="collection_name", param_type="string"),
                    Param(name="data_source_fqn", param_type="string"),
                    Param(name="data_ingestion_run_name", param_type="string"),
                    Param(
                        name="data_ingestion_mode",
                        default="INCREMENTAL",
                        param_type="string",
                    ),
                    Param(
                        name="raise_error_on_failure",
                        default="False",
                        param_type="string",
                    ),
                ],
                env={
                    "LOG_LEVEL": "DEBUG",
                    "DATABASE_URL": f"postgresql://admin:password@{DATABASE_NAME}-postgresql.{workspace}.svc.cluster.local:5432/cognita-config",
                    "ML_REPO_NAME": ml_repo,
                    "VECTOR_DB_CONFIG": VECTOR_DB_CONFIG,
                    "CARBON_AI_API_KEY": "tfy-secret://internal:cognita:CARBON_AI_API_KEY",
                    "MODELS_CONFIG_PATH": "./models_config.truefoundry.yaml",
                    "METADATA_STORE_CONFIG": '{"provider":"prisma"}',
                    "INFINITY_API_KEY": "tfy-secret://internal:cognita:INFINITY_API_KEY",
                    "UNSTRUCTURED_IO_URL": f"http://{UNSTRUCTURED_IO_SERVICE_NAME}.{workspace}.svc.cluster.local:8000",
                    "UNSTRUCTURED_IO_API_KEY": "tfy-secret://internal:cognita:UNSTRUCTURED_IO_API_KEY",
                },
                resources=Resources(
                    cpu_request=1.0,
                    cpu_limit=1.5,
                    memory_request=1500,
                    memory_limit=2000,
                    ephemeral_storage_request=1000,
                    ephemeral_storage_limit=2000,
                    node=NodeSelector(capacity_type="spot_fallback_on_demand"),
                ),
                retries=0,
                mounts=[],
            ),
            Service(
                name=BACKEND_SERVICE_NAME,
                image=Build(
                    build_source=LocalSource(local_build=False),
                    build_spec=DockerFileBuild(
                        dockerfile_path="./backend/Dockerfile",
                        build_context_path="./",
                        command='/bin/bash -c "set -e; prisma db push --schema ./backend/database/schema.prisma && uvicorn --host 0.0.0.0 --port 8000 backend.server.app:app"',
                    ),
                ),
                resources=Resources(
                    cpu_request=0.8,
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
                    "ML_REPO_NAME": ml_repo,
                    "VECTOR_DB_CONFIG": VECTOR_DB_CONFIG,
                    "JOB_COMPONENT_NAME": f"{workspace}-{INDEXER_SERVICE_NAME}",
                    "MODELS_CONFIG_PATH": "./models_config.truefoundry.yaml",
                    "METADATA_STORE_CONFIG": '{"provider":"prisma"}',
                    "UNSTRUCTURED_IO_URL": f"http://{UNSTRUCTURED_IO_SERVICE_NAME}.{workspace}.svc.cluster.local:8000",
                    "UNSTRUCTURED_IO_API_KEY": "tfy-secret://internal:cognita:UNSTRUCTURED_IO_API_KEY",
                    "BRAVE_API_KEY": "tfy-secret://internal:cognita:BRAVE_API_KEY",
                    "INFINITY_API_KEY": "tfy-secret://internal:cognita:INFINITY_API_KEY",
                    "CARBON_AI_API_KEY": "tfy-secret://internal:cognita:CARBON_AI_API_KEY",
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
                        data=f"""
                            model_providers:
                            - provider_name: truefoundry
                                api_format: openai
                                base_url: https://llm-gateway.truefoundry.com/api/inference/openai
                                api_key_env_var: TFY_API_KEY
                                llm_model_ids:
                                - "openai-main/gpt-4o-mini"
                                - "openai-main/gpt-4o"
                                - "openai-main/gpt-4-turbo"
                                - "azure-openai/gpt-4"
                                - "together-ai/llama-3-70b-chat-hf"
                                embedding_model_ids:
                                - "openai-main/text-embedding-3-small"
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
                        """,
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
            ),
            Service(
                name=FRONTEND_SERVICE_NAME,
                image=Build(
                    build_source=LocalSource(local_build=False),
                    build_spec=DockerFileBuild(
                        dockerfile_path="./frontend/Dockerfile",
                        build_context_path="./frontend",
                        build_args={
                            "VITE_CARBON_API_KEY": "tfy-secret://internal:cognita:CARBON_AI_API_KEY",
                            "VITE_QA_FOUNDRY_URL": f"https://{application_set_name}.{base_domain_url}/api",
                            "VITE_DOCS_QA_STANDALONE_PATH": "/",
                            "VITE_DOCS_QA_ENABLE_STANDALONE": "true",
                            "VITE_DOCS_QA_DELETE_COLLECTIONS": "true",
                            "VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB": 200,
                        },
                    ),
                ),
                resources=Resources(
                    cpu_request=0.05,
                    cpu_limit=0.1,
                    memory_request=100,
                    memory_limit=200,
                    ephemeral_storage_request=100,
                    ephemeral_storage_limit=200,
                ),
                ports=[
                    Port(
                        port=5000,
                        protocol="TCP",
                        expose=True,
                        app_protocol="http",
                        host=f"{application_set_name}.{base_domain_url}",
                    )
                ],
                replicas=1.0,
                allow_interception=False,
            ),
            Helm(
                name=VECTOR_DB_HELM_NAME,
                source=HelmRepo(
                    repo_url="https://qdrant.github.io/qdrant-helm",
                    chart="qdrant",
                    version="0.8.4",
                ),
                values={
                    "service": {
                        "type": "ClusterIP",
                        "ports": [
                            {
                                "name": "http",
                                "port": 6333,
                                "protocol": "TCP",
                                "targetPort": 6333,
                                "checksEnabled": True,
                            },
                            {
                                "name": "grpc",
                                "port": 6334,
                                "protocol": "TCP",
                                "targetPort": 6334,
                                "checksEnabled": False,
                            },
                            {
                                "name": "http-p2p",
                                "port": 6335,
                                "protocol": "TCP",
                                "targetPort": 6335,
                                "checksEnabled": False,
                            },
                        ],
                    },
                    "persistence": {"size": "50G"},
                    "tolerations": [
                        {
                            "key": "kubernetes.azure.com/scalesetpriority",
                            "value": "spot",
                            "effect": "NoSchedule",
                            "operator": "Equal",
                        },
                        {
                            "key": "cloud.google.com/gke-spot",
                            "value": "true",
                            "effect": "NoSchedule",
                            "operator": "Equal",
                        },
                    ],
                    "replicaCount": 2,
                    "fullnameOverride": VECTOR_DB_HELM_NAME,
                },
                kustomize=Kustomize(
                    additions=[
                        {
                            "kind": "VirtualService",
                            "spec": {
                                "http": [
                                    {
                                        "match": [{"uri": {"prefix": "/qdrant/"}}],
                                        "route": [
                                            {
                                                "destination": {
                                                    "host": f"{VECTOR_DB_HELM_NAME}.{workspace}.svc.cluster.local",
                                                    "port": {"number": 6333},
                                                }
                                            }
                                        ],
                                        "rewrite": {"uri": "/"},
                                    },
                                    {
                                        "match": [
                                            {
                                                "headers": {
                                                    "x-route-service": {
                                                        "exact": "qdrant-ui"
                                                    }
                                                }
                                            }
                                        ],
                                        "route": [
                                            {
                                                "destination": {
                                                    "host": f"{VECTOR_DB_HELM_NAME}.{workspace}.svc.cluster.local",
                                                    "port": {"number": 6333},
                                                }
                                            }
                                        ],
                                        "rewrite": {"uri": "/"},
                                    },
                                ],
                                "hosts": [
                                    f"{QDRANT_SERVICE_UI_NAME}.{base_domain_url}"
                                ],
                                "gateways": ["istio-system/tfy-wildcard"],
                            },
                            "metadata": {
                                "name": VECTOR_DB_HELM_NAME,
                                "namespace": workspace,
                            },
                            "apiVersion": "networking.istio.io/v1alpha3",
                        }
                    ]
                ),
            ),
            Service(
                name=QDRANT_SERVICE_UI_NAME,
                image=Build(
                    build_source=GitSource(
                        repo_url="https://github.com/truefoundry/qdrant-web-ui-new",
                        ref="038f5a4db22b54459e1820ab2ec51771f8f09919",
                        branch_name="support-path-based-routing",
                    ),
                    build_spec=DockerFileBuild(
                        dockerfile_path="./Dockerfile",
                        build_context_path="./",
                    ),
                ),
                resources=Resources(
                    cpu_request=0.2,
                    cpu_limit=0.5,
                    memory_request=200,
                    memory_limit=500,
                    ephemeral_storage_request=1000,
                    ephemeral_storage_limit=2000,
                    node=NodeSelector(capacity_type="spot_fallback_on_demand"),
                ),
                ports=[
                    Port(
                        port=3000,
                        protocol="TCP",
                        expose=True,
                        app_protocol="http",
                        host=f"{QDRANT_SERVICE_UI_NAME}.{base_domain_url}",
                        path="/qdrant-ui/",
                    )
                ],
                mounts=[],
                replicas=1.0,
                allow_interception=False,
            ),
            Service(
                name=UNSTRUCTURED_IO_SERVICE_NAME,
                image=Image(
                    image_uri="downloads.unstructured.io/unstructured-io/unstructured-api:0.0.73",
                ),
                resources=Resources(
                    cpu_request=0.8,
                    cpu_limit=1.5,
                    memory_request=4000,
                    memory_limit=8000,
                    ephemeral_storage_request=1500,
                    ephemeral_storage_limit=2000,
                    node=NodeSelector(capacity_type="spot_fallback_on_demand"),
                ),
                env={
                    "UNSTRUCTURED_API_KEY": "tfy-secret://internal:cognita:UNSTRUCTURED_IO_API_KEY"
                },
                ports=[
                    Port(port=8000, protocol="TCP", expose=False, app_protocol="http")
                ],
                mounts=[],
                replicas=2.0,
                allow_interception=False,
            ),
            Service(
                name=INFINITY_SERVICE_NAME,
                image=Image(
                    image_uri="michaelf34/infinity:0.0.54",
                    command="infinity_emb v2 --model-id mixedbread-ai/mxbai-embed-large-v1 --model-id mixedbread-ai/mxbai-rerank-xsmall-v1 --port $(PORT) --batch-size $(BATCH_SIZE) --api-key $(API_KEY)",
                ),
                resources=Resources(
                    cpu_request=0.8,
                    cpu_limit=1.0,
                    memory_request=4000,
                    memory_limit=8000,
                    ephemeral_storage_request=1500,
                    ephemeral_storage_limit=2000,
                    node=NodeSelector(capacity_type="spot_fallback_on_demand"),
                ),
                env={
                    "PORT": "8000",
                    "API_KEY": "tfy-secret://internal:cognita:INFINITY_API_KEY",
                    "BATCH_SIZE": "4",
                },
                ports=[
                    Port(port=8000, protocol="TCP", expose=False, app_protocol="http")
                ],
                mounts=[],
                replicas=2.0,
                allow_interception=False,
            ),
            Helm(
                name=DATABASE_NAME,
                source=OCIRepo(
                    oci_chart_url="oci://registry-1.docker.io/bitnamicharts/postgresql",
                    version="13.4.3",
                ),
                values={
                    "auth": {
                        "database": "cognita-config",
                        "password": "password",
                        "username": "admin",
                        "postgresPassword": "password",
                        "enablePostgresUser": True,
                    },
                    "primary": {
                        "service": {"ports": {"postgresql": 5432}},
                        "resources": {
                            "limits": {"cpu": "100m", "memory": "256Mi"},
                            "requests": {"cpu": "100m", "memory": "256Mi"},
                        },
                        "persistence": {"size": "5Gi"},
                    },
                    "architecture": "standalone",
                },
            ),
        ],
        workspace_fqn=workspace_fqn,
    )
    application_set.deploy(workspace_fqn=workspace_fqn, wait=False)


if __name__ == "__main__":
    # Setup the argument parser by instantiating `ArgumentParser` class
    parser = argparse.ArgumentParser()
    # Add the parameters as arguments
    parser.add_argument(
        "--workspace_fqn",
        type=str,
        required=True,
        help="The workspace FQN where the application set will be deployed",
    )
    parser.add_argument(
        "--application_set_name", type=str, help="Name of the application set"
    )
    parser.add_argument(
        "--ml_repo",
        type=str,
        required=True,
        help="""The name of the ML Repo to track metrics and models.
            You can create one from the ML Repos Tab on the UI.
            Docs: https://docs.truefoundry.com/docs/key-concepts#creating-an-ml-repo""",
    )
    parser.add_argument(
        "--base_domain_url",
        type=str,
        required=True,
        help="The host name of the application set.",
    )

    args = parser.parse_args()

    run_deploy(**vars(args))


### To run the script, run the following command
### python -m deployment.backend_deploy --workspace_fqn <> --application_set_name <> --ml_repo <> --base_domain_url <>
