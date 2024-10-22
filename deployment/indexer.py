from truefoundry.deploy import (
    Build,
    DockerFileBuild,
    Job,
    LocalSource,
    Manual,
    NodeSelector,
    Param,
    Resources,
)

from deployment.config import (
    DATABASE_NAME,
    INDEXER_SERVICE_NAME,
    INFINITY_SERVICE_NAME,
    UNSTRUCTURED_IO_SERVICE_NAME,
)


class Indexer:
    def __init__(
        self,
        secrets_base,
        ml_repo,
        workspace,
        application_set_name,
        VECTOR_DB_CONFIG,
        base_domain_url,
    ):
        self.secrets_base = secrets_base
        self.ml_repo = ml_repo
        self.workspace = workspace
        self.VECTOR_DB_CONFIG = VECTOR_DB_CONFIG
        self.application_set_name = application_set_name
        self.base_domain_url = base_domain_url

    def create_job(self):
        INDEXER_COMMAND = """/bin/bash -c 'set -e; prisma generate --schema ./backend/database/schema.prisma && python -m backend.indexer.main  --collection_name "{{collection_name}}" --data_source_fqn "{{data_source_fqn}}" --data_ingestion_run_name "{{data_ingestion_run_name}}" --data_ingestion_mode "{{data_ingestion_mode}}" --raise_error_on_failure  "{{raise_error_on_failure}}"'"""
        return Job(
            name=f"{self.application_set_name}-{INDEXER_SERVICE_NAME}",
            image=Build(
                build_source=LocalSource(local_build=False),
                build_spec=DockerFileBuild(
                    dockerfile_path="./backend/Dockerfile",
                    build_context_path="./",
                    command=INDEXER_COMMAND,
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
                    name="raise_error_on_failure", default="False", param_type="string"
                ),
            ],
            env={
                "LOG_LEVEL": "DEBUG",
                "DATABASE_URL": f"postgresql://admin:password@{self.application_set_name}-{DATABASE_NAME}-postgresql.{self.workspace}.svc.cluster.local:5432/cognita-config",
                "INFINITY_URL": f"http://{self.application_set_name}-{INFINITY_SERVICE_NAME}.{self.workspace}.svc.cluster.local:8000",
                "ML_REPO_NAME": self.ml_repo,
                "BRAVE_API_KEY": f"{self.secrets_base}:BRAVE-API-KEY",
                "INFINITY_API_KEY": f"{self.secrets_base}:INFINITY-API-KEY",
                "VECTOR_DB_CONFIG": self.VECTOR_DB_CONFIG,
                "MODELS_CONFIG_PATH": "./models_config.truefoundry.yaml",
                "UNSTRUCTURED_IO_URL": f"http://{self.application_set_name}-{UNSTRUCTURED_IO_SERVICE_NAME}.{self.workspace}.svc.cluster.local:8000",
                "METADATA_STORE_CONFIG": '{"provider":"prisma"}',
                "UNSTRUCTURED_IO_API_KEY": f"{self.secrets_base}:UNSTRUCTURED-IO-API-KEY",
                "TFY_API_KEY": f"{self.secrets_base}:TFY-API-KEY",
                "TFY_HOST": f"{self.secrets_base}:TFY-HOST",
            },
            resources=Resources(
                cpu_request=1.0,
                cpu_limit=1.5,
                memory_request=1000,
                memory_limit=1500,
                ephemeral_storage_request=1000,
                ephemeral_storage_limit=2000,
                node=NodeSelector(capacity_type="spot_fallback_on_demand"),
            ),
            retries=0,
            mounts=[],
        )
