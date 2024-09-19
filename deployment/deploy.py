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


def run_deploy(workspace_fqn, application_set_name, ml_repo, base_domain_url):
    workspace = workspace_fqn.split(":")[1]
    VECTOR_DB_CONFIG = json.dumps(
        {
            "provider": "qdrant",
            "url": f"http://{VECTOR_DB_HELM_NAME}.{workspace}.svc.cluster.local:6333",
            "api_key": "",
        }
    )

    application_set = ApplicationSet(
        name=application_set_name,
        components=[
            Indexer(
                ml_repo=ml_repo, workspace=workspace, VECTOR_DB_CONFIG=VECTOR_DB_CONFIG
            ).create_job(),
            Backend(
                ml_repo=ml_repo,
                workspace_fqn=workspace_fqn,
                workspace=workspace,
                application_set_name=application_set_name,
                base_domain_url=base_domain_url,
                VECTOR_DB_CONFIG=VECTOR_DB_CONFIG,
            ).create_service(),
            Frontend(
                application_set_name=application_set_name,
                base_domain_url=base_domain_url,
            ).create_service(),
            Qdrant(workspace=workspace, base_domain_url=base_domain_url).create_helm(),
            QdrantUI(base_domain_url=base_domain_url).create_service(),
            UnstructuredIO().create_service(),
            Infinity().create_service(),
            PostgresDatabase().create_helm(),
            Audio().create_service(),
        ],
        workspace_fqn=workspace_fqn,
    )
    application_set.deploy(workspace_fqn=workspace_fqn, wait=False)


if __name__ == "__main__":
    # print(Infinity().create_service())
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
        "--base_domain_url",
        type=str,
        required=True,
        help="""\
            The host name of the application set.
        """,
    )

    args = parser.parse_args()

    run_deploy(**vars(args))


### To run the script, run the following command
### python -m deployment.backend_deploy --workspace_fqn tfy-devtest-euwe1:jitender-ws --application_set_name backend-test --ml_repo cognita-testing --base_domain_url devtest.truefoundry.tech
