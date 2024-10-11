import argparse
import json
import logging

from truefoundry.deploy import Image, NodeSelector, Port, Resources, Service

from deployment.config import UNSTRUCTURED_IO_SERVICE_NAME


class UnstructuredIO:
    def __init__(self):
        pass

    def create_service(self):
        return Service(
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
            ports=[Port(port=8000, protocol="TCP", expose=False, app_protocol="http")],
            mounts=[],
            replicas=2.0,
            allow_interception=False,
        )
