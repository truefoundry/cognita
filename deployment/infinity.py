from truefoundry.deploy import Image, NodeSelector, Port, Resources, Service

from deployment.config import INFINITY_SERVICE_NAME


class Infinity:
    def __init__(self):
        pass

    def create_service(self):
        return Service(
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
            ports=[Port(port=8000, protocol="TCP", expose=False, app_protocol="http")],
            mounts=[],
            replicas=2.0,
            allow_interception=False,
        )
