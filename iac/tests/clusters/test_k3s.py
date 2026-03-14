import cdk8s

from lab.clusters.k3s import K3sCluster
from lab.libs.config import K3sClusterConfig


class TestK3sCluster:
    def test_initializes_without_error(self) -> None:
        app = cdk8s.Testing.app()
        K3sCluster(app, K3sClusterConfig())
