from truefoundry.deploy import Image, NodepoolSelector, Port, Resources, Service

from deployment.config import UNSTRUCTURED_IO_SERVICE_NAME


class UnstructuredIO:
    def __init__(self, secrets_base, application_set_name):
        self.secrets_base = secrets_base
        self.application_set_name = application_set_name

    def create_service(self):
        return Service(
            name=f"{self.application_set_name}-{UNSTRUCTURED_IO_SERVICE_NAME}",
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
                node=NodepoolSelector(),
            ),
            env={
                "UNSTRUCTURED_API_KEY": f"{self.secrets_base}:UNSTRUCTURED-IO-API-KEY"
            },
            ports=[Port(port=8000, protocol="TCP", expose=False, app_protocol="http")],
            mounts=[],
            replicas=2.0,
            allow_interception=False,
        )
