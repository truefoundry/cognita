from truefoundry.deploy import Image, NodeSelector, Port, Resources, Service

from deployment.config import INFINITY_SERVICE_NAME


class Infinity:
    def __init__(self, secrets_base, application_set_name, dockerhub_images_registry):
        self.secrets_base = secrets_base
        self.application_set_name = application_set_name
        self.dockerhub_images_registry = dockerhub_images_registry

    def create_service(self):
        return Service(
            name=f"{self.application_set_name}-{INFINITY_SERVICE_NAME}",
            image=Image(
                image_uri=f"{self.dockerhub_images_registry}/michaelf34/infinity:0.0.63",
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
                "API_KEY": f"{self.secrets_base}:INFINITY-API-KEY",
                "BATCH_SIZE": "4",
            },
            ports=[Port(port=8000, protocol="TCP", expose=False, app_protocol="http")],
            mounts=[],
            replicas=2.0,
            allow_interception=False,
        )
