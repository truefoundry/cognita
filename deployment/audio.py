from truefoundry.deploy import (
    HealthProbe,
    HttpProbe,
    Image,
    NodeSelector,
    Port,
    Resources,
    Service,
)

from deployment.config import AUDIO_SERVICE_NAME


class Audio:
    def __init__(self, application_set_name, dockerhub_images_registry):
        self.dockerhub_images_registry = dockerhub_images_registry
        self.application_set_name = application_set_name

    def create_service(self):
        return Service(
            name=f"{self.application_set_name}-{AUDIO_SERVICE_NAME}",
            image=Image(
                type="image",
                image_uri=f"{self.dockerhub_images_registry}/fedirz/faster-whisper-server:latest-cpu",
            ),
            resources=Resources(
                node=NodeSelector(capacity_type="spot_fallback_on_demand"),
                cpu_limit=1,
                cpu_request=0.8,
                memory_limit=8000,
                memory_request=4000,
                ephemeral_storage_limit=4000,
                ephemeral_storage_request=2500,
            ),
            env={
                "WHISPER_PORT": 8000,
                "WHISPER__MODEL": "Systran/faster-distil-whisper-large-v3",
                "WHISPER__INFERENCE_DEVICE": "auto",
            },
            ports=[
                Port(port=8000, expose=False, protocol="TCP", app_protocol="http"),
            ],
            mounts=[],
            liveness_probe=HealthProbe(
                config=HttpProbe(path="/health", port=8000, scheme="HTTP"),
                period_seconds=60,
                timeout_seconds=2,
                failure_threshold=5,
                success_threshold=1,
                initial_delay_seconds=10,
            ),
            readiness_probe=HealthProbe(
                config=HttpProbe(path="/health", port=8000, scheme="HTTP"),
                period_seconds=30,
                timeout_seconds=2,
                failure_threshold=5,
                success_threshold=1,
                initial_delay_seconds=10,
            ),
            replicas=1,
            allow_interception=False,
        )
