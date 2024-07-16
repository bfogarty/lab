from constructs import Construct

from cdk8s import ApiObjectMetadata, Chart, Helm

import cdk8s_plus_29 as kplus
from lab.libs.config import GrafanaConfig


class GrafanaAlloy(Chart):
    VERSION = "1.30.5"

    NAMESPACE = "grafana"

    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        config: GrafanaConfig,
    ):
        super().__init__(scope, id_, namespace=GrafanaAlloy.NAMESPACE)

        kplus.Namespace(
            self, id_, metadata=ApiObjectMetadata(name=GrafanaAlloy.NAMESPACE)
        )

        Helm(
            self,
            f"{id_}-helm",
            repo="https://grafana.github.io/helm-charts",
            chart="k8s-monitoring",
            namespace=GrafanaAlloy.NAMESPACE,
            helm_flags=["--skip-tests", "--no-hooks"],
            values={
                "cluster": {"name": "lab"},
                "externalServices": {
                    "prometheus": {
                        "host": config.prometheus.host,
                        "basicAuth": {
                            "username": config.prometheus.username,
                            "password": config.access_policy_token.get_secret_value(),
                        },
                    },
                    "loki": {
                        "host": config.loki.host,
                        "basicAuth": {
                            "username": config.loki.username,
                            "password": config.access_policy_token.get_secret_value(),
                        },
                    },
                },
                "metrics": {
                    "enabled": True,
                    "cost": {"enabled": True},
                    "node-exporter": {"enabled": True},
                },
                "logs": {
                    "enabled": True,
                    "pod_logs": {"enabled": True},
                    "cluster_events": {"enabled": True},
                },
                "traces": {"enabled": False},
                "receivers": {
                    "grpc": {"enabled": False},
                    "http": {"enabled": False},
                    "zipkin": {"enabled": False},
                    "grafanaCloudMetrics": {"enabled": False},
                },
                "opencost": {
                    "enabled": True,
                    "opencost": {
                        "exporter": {"defaultClusterId": "lab"},
                        "prometheus": {
                            "external": {"url": f"{config.prometheus.host}/api/prom"}
                        },
                    },
                },
                "kube-state-metrics": {"enabled": True},
                "prometheus-node-exporter": {"enabled": True},
                "prometheus-operator-crds": {"enabled": True},
                "alloy": {},
                "alloy-events": {},
                "alloy-logs": {},
            },
        )
