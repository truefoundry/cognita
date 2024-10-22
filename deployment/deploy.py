import argparse
import json
import logging

from truefoundry.deploy import ApplicationSet

from deployment.audio import Audio
from deployment.backend import Backend
from deployment.config import VECTOR_DB_HELM_NAME
from deployment.frontend import Frontend
from deployment.indexer import Indexer
from deployment.infinity import Infinity
from deployment.postgres_database import PostgresDatabase
from deployment.qdrant import Qdrant
from deployment.qdrant_ui import QdrantUI
from deployment.unstructured_io import UnstructuredIO

logging.basicConfig(level=logging.INFO)


def run_deploy(
    workspace_fqn,
    application_set_name,
    ml_repo,
    base_domain_url,
    dockerhub_images_registry,
    secrets_base,
):
    workspace = workspace_fqn.split(":")[1]
    VECTOR_DB_CONFIG = json.dumps(
        {
            "provider": "qdrant",
            "url": f"http://{application_set_name}-{VECTOR_DB_HELM_NAME}.{workspace}.svc.cluster.local:6333",
            "api_key": "",
        }
    )

    application_set = ApplicationSet(
        name=application_set_name,
        components=[
            Indexer(
                secrets_base=secrets_base,
                ml_repo=ml_repo,
                workspace=workspace,
                application_set_name=application_set_name,
                VECTOR_DB_CONFIG=VECTOR_DB_CONFIG,
                base_domain_url=base_domain_url,
            ).create_job(),
            Backend(
                secrets_base=secrets_base,
                ml_repo=ml_repo,
                workspace_fqn=workspace_fqn,
                workspace=workspace,
                application_set_name=application_set_name,
                base_domain_url=base_domain_url,
                VECTOR_DB_CONFIG=VECTOR_DB_CONFIG,
            ).create_service(),
            Frontend(
                secrets_base=secrets_base,
                application_set_name=application_set_name,
                base_domain_url=base_domain_url,
            ).create_service(),
            Qdrant(
                secrets_base=secrets_base,
                workspace=workspace,
                application_set_name=application_set_name,
                base_domain_url=base_domain_url,
                dockerhub_images_registry=dockerhub_images_registry,
            ).create_helm(),
            QdrantUI(
                secrets_base=secrets_base,
                application_set_name=application_set_name,
                base_domain_url=base_domain_url,
            ).create_service(),
            UnstructuredIO(
                secrets_base=secrets_base,
                application_set_name=application_set_name,
            ).create_service(),
            Infinity(
                secrets_base=secrets_base,
                application_set_name=application_set_name,
                dockerhub_images_registry=dockerhub_images_registry,
            ).create_service(),
            PostgresDatabase(
                secrets_base=secrets_base,
                application_set_name=application_set_name,
                dockerhub_images_registry=dockerhub_images_registry,
            ).create_helm(),
            Audio(
                secrets_base=secrets_base,
                application_set_name=application_set_name,
                dockerhub_images_registry=dockerhub_images_registry,
            ).create_service(),
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
        help="""\
            The name of the ML Repo to track metrics and models.
            You can create one from the ML Repos Tab on the UI.
            Docs: https://docs.truefoundry.com/docs/key-concepts#creating-an-ml-repo,
        """,
    )
    parser.add_argument(
        "--base_domain_url", type=str, required=True, help="cluster base domain url"
    )

    parser.add_argument(
        "--dockerhub-images-registry",
        type=str,
        required=False,
        help="dockerhub images registry",
        default="docker.io",
    )

    parser.add_argument(
        "--secrets-base",
        type=str,
        required=False,
        help="base path for secrets store",
        default="tfy-secret://internal:cognita",
    )

    args = parser.parse_args()

    run_deploy(**vars(args))


### To run the script, run the following command
### python -m deployment.deploy --workspace_fqn <worksapce> --application_set_name <application_set_name> --ml_repo <ml_repo> --base_domain_url <cluster base domain url> --dockerhub-images-registry <dockerhub images registry>
