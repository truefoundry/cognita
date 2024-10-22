from truefoundry.deploy import (
    Build,
    DockerFileBuild,
    GitSource,
    NodepoolSelector,
    Port,
    Resources,
    Service,
)

from deployment.config import QDRANT_SERVICE_UI_NAME


class QdrantUI:
    def __init__(self, secrets_base, application_set_name, base_domain_url):
        self.secrets_base = secrets_base
        self.application_set_name = application_set_name
        self.base_domain_url = base_domain_url

    def create_service(self):
        name = f"{self.application_set_name}-{QDRANT_SERVICE_UI_NAME}"
        return Service(
            name=name,
            image=Build(
                # Set build_source=LocalSource(local_build=False), in order to deploy code from your local.
                # With local_build=False flag, docker image will be built on cloud instead of local
                # Else it will try to use docker installed on your local machine to build the image
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
                node=NodepoolSelector(),
            ),
            ports=[
                Port(
                    port=3000,
                    protocol="TCP",
                    expose=True,
                    app_protocol="http",
                    host=f"{name}.{self.base_domain_url}",
                    path="/qdrant-ui/",
                )
            ],
            mounts=[],
            replicas=1.0,
            allow_interception=False,
        )
