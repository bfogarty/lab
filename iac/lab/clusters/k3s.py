from cdk8s import App

from lab.clusters.base import BaseCluster
from lab.libs.config import K3sClusterConfig


class K3sCluster(BaseCluster):
    config_class = K3sClusterConfig

    def __init__(self, app: App, config: K3sClusterConfig) -> None:
        pass
