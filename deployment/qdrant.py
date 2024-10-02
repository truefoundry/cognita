from truefoundry.deploy import Helm, HelmRepo, Kustomize

from deployment.config import QDRANT_SERVICE_UI_NAME, VECTOR_DB_HELM_NAME


class Qdrant:
    def __init__(self, workspace, base_domain_url):
        self.workspace = workspace
        self.base_domain_url = base_domain_url

    def create_helm(self):
        return Helm(
            name=VECTOR_DB_HELM_NAME,
            source=HelmRepo(
                repo_url="https://qdrant.github.io/qdrant-helm",
                chart="qdrant",
                version="0.8.4",
            ),
            values={
                "service": {
                    "type": "ClusterIP",
                    "ports": [
                        {
                            "name": "http",
                            "port": 6333,
                            "protocol": "TCP",
                            "targetPort": 6333,
                            "checksEnabled": True,
                        },
                        {
                            "name": "grpc",
                            "port": 6334,
                            "protocol": "TCP",
                            "targetPort": 6334,
                            "checksEnabled": False,
                        },
                        {
                            "name": "http-p2p",
                            "port": 6335,
                            "protocol": "TCP",
                            "targetPort": 6335,
                            "checksEnabled": False,
                        },
                    ],
                },
                "persistence": {"size": "50G"},
                "tolerations": [
                    {
                        "key": "kubernetes.azure.com/scalesetpriority",
                        "value": "spot",
                        "effect": "NoSchedule",
                        "operator": "Equal",
                    },
                    {
                        "key": "cloud.google.com/gke-spot",
                        "value": "true",
                        "effect": "NoSchedule",
                        "operator": "Equal",
                    },
                ],
                "replicaCount": 2,
                "fullnameOverride": VECTOR_DB_HELM_NAME,
            },
            kustomize=Kustomize(
                additions=[
                    {
                        "kind": "VirtualService",
                        "spec": {
                            "http": [
                                {
                                    "match": [{"uri": {"prefix": "/qdrant/"}}],
                                    "route": [
                                        {
                                            "destination": {
                                                "host": f"{VECTOR_DB_HELM_NAME}.{self.workspace}.svc.cluster.local",
                                                "port": {"number": 6333},
                                            }
                                        }
                                    ],
                                    "rewrite": {"uri": "/"},
                                },
                                {
                                    "match": [
                                        {
                                            "headers": {
                                                "x-route-service": {
                                                    "exact": "qdrant-ui"
                                                }
                                            }
                                        }
                                    ],
                                    "route": [
                                        {
                                            "destination": {
                                                "host": f"{VECTOR_DB_HELM_NAME}.{self.workspace}.svc.cluster.local",
                                                "port": {"number": 6333},
                                            }
                                        }
                                    ],
                                    "rewrite": {"uri": "/"},
                                },
                            ],
                            "hosts": [
                                f"{QDRANT_SERVICE_UI_NAME}.{self.base_domain_url}"
                            ],
                            "gateways": ["istio-system/tfy-wildcard"],
                        },
                        "metadata": {
                            "name": VECTOR_DB_HELM_NAME,
                            "namespace": self.workspace,
                        },
                        "apiVersion": "networking.istio.io/v1alpha3",
                    }
                ]
            ),
        )
