from truefoundry.deploy import Helm, OCIRepo

from deployment.config import DATABASE_NAME


class PostgresDatabase:
    def __init__(self, dockerhub_images_registry):
        self.dockerhub_images_registry = dockerhub_images_registry

    def create_helm(self):
        return Helm(
            name=DATABASE_NAME,
            source=OCIRepo(
                oci_chart_url="oci://registry-1.docker.io/bitnamicharts/postgresql",
                version="13.4.3",
            ),
            values={
                "global": {"imageRegistry": self.dockerhub_images_registry},
                "auth": {
                    "database": "cognita-config",
                    "password": "password",
                    "username": "admin",
                    "postgresPassword": "password",
                    "enablePostgresUser": True,
                },
                "primary": {
                    "service": {"ports": {"postgresql": 5432}},
                    "resources": {
                        "limits": {"cpu": "100m", "memory": "256Mi"},
                        "requests": {"cpu": "100m", "memory": "256Mi"},
                    },
                    "persistence": {"size": "5Gi"},
                },
                "architecture": "standalone",
            },
        )
