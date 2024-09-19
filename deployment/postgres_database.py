from truefoundry.deploy import Helm, OCIRepo

from deployment.config import DATABASE_NAME


class PostgresDatabase:
    def __init__(self):
        pass

    def create_helm(self):
        return Helm(
            name=DATABASE_NAME,
            source=OCIRepo(
                oci_chart_url="oci://registry-1.docker.io/bitnamicharts/postgresql",
                version="13.4.3",
            ),
            values={
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
