from truefoundry.deploy import (
    Build,
    DockerFileBuild,
    LocalSource,
    Port,
    Resources,
    Service,
)

from deployment.config import FRONTEND_SERVICE_NAME


class Frontend:
    def __init__(self, secrets_base, application_set_name, base_domain_url):
        self.secrets_base = secrets_base
        self.application_set_name = application_set_name
        self.base_domain_url = base_domain_url

    def create_service(self):
        return Service(
            name=f"{self.application_set_name}-{FRONTEND_SERVICE_NAME}",
            image=Build(
                # Set build_source=LocalSource(local_build=False), in order to deploy code from your local.
                # With local_build=False flag, docker image will be built on cloud instead of local
                # Else it will try to use docker installed on your local machine to build the image
                build_source=LocalSource(local_build=False),
                build_spec=DockerFileBuild(
                    dockerfile_path="./frontend/Dockerfile",
                    build_context_path="./frontend",
                    build_args={
                        "VITE_QA_FOUNDRY_URL": f"https://{self.application_set_name}.{self.base_domain_url}/api",
                        "VITE_DOCS_QA_STANDALONE_PATH": "/",
                        "VITE_DOCS_QA_ENABLE_STANDALONE": "true",
                        "VITE_DOCS_QA_DELETE_COLLECTIONS": "true",
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
                    host=f"{self.application_set_name}.{self.base_domain_url}",
                )
            ],
            replicas=1.0,
            allow_interception=False,
        )
