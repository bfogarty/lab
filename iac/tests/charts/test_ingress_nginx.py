from collections.abc import Generator
from typing import Any
from lab.charts.ingress_nginx import IngressNginx
import pytest
import cdk8s

from lab.libs.config import IngressConfig
from tests.utils import get_resource


NSG_OCID = "ocid"


class TestIngressNginx:
    @pytest.fixture(scope="class")
    def chart(self) -> Generator[list[Any], None, None]:
        yield IngressNginx(
            cdk8s.Testing.app(),
            "ingress-nginx",
            config=IngressConfig(
                oci_public_load_balancer_nsg_ocid=NSG_OCID,
            ),
        ).to_json()

    def test_includes_deployment(self, chart: list[Any]) -> None:
        assert get_resource(chart, "Deployment", "ingress-nginx-controller")

    def test_service_uses_nlb(self, chart: list[Any]) -> None:
        svc = get_resource(chart, "Service", "ingress-nginx-controller")
        assert {
            "oci.oraclecloud.com/load-balancer-type": "nlb",
            "oci-network-load-balancer.oraclecloud.com/oci-network-security-groups": NSG_OCID,
        } == svc["metadata"]["annotations"]

    def test_snippets_are_enabled(self, chart: list[Any]) -> None:
        cfg = get_resource(chart, "ConfigMap", "ingress-nginx-controller")
        assert bool(cfg["data"]["allow-snippet-annotations"])
