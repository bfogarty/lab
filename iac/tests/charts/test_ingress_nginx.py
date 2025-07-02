from collections.abc import Generator
from typing import Any
from unittest.mock import Mock, patch
from lab.charts.ingress_nginx import IngressNginx
import pytest
import cdk8s

from lab.libs.config import IngressConfig
from lab.libs.exceptions import LabError
from tests.utils import get_resource


CONFIG = IngressConfig(
    oci_public_load_balancer_nsg_ocid="ocid",
)

class TestIngressNginx:
    @pytest.fixture(scope="class")
    def chart(self) -> Generator[list[Any], None, None]:
        yield IngressNginx(
            cdk8s.Testing.app(),
            "ingress-nginx",
            config=CONFIG,
        ).to_json()

    def test_includes_deployment(self, chart: list[Any]) -> None:
        assert get_resource(chart, "Deployment", "ingress-nginx-controller")

    def test_service_uses_nlb(self, chart: list[Any]) -> None:
        svc = get_resource(chart, "Service", "ingress-nginx-controller")
        assert {
            "oci.oraclecloud.com/load-balancer-type": "nlb",
            "oci-network-load-balancer.oraclecloud.com/oci-network-security-groups": CONFIG.oci_public_load_balancer_nsg_ocid,
        } == svc["metadata"]["annotations"]

    def test_snippets_are_enabled(self, chart: list[Any]) -> None:
        cfg = get_resource(chart, "ConfigMap", "ingress-nginx-controller")
        assert bool(cfg["data"]["allow-snippet-annotations"])
        assert "Critical" == cfg["data"]["annotations-risk-level"]

    @patch("cdk8s.ApiObject.to_json")
    def test_cannot_override_default_service_annotations(self, mocked_to_json: Mock) -> None:
        mocked_to_json.return_value = {
            "metadata": {
                "annotations": {"foo": "bar"},
            }
        }

        with pytest.raises(LabError, match="Service has annotations"):
            IngressNginx(
                cdk8s.Testing.app(),
                "ingress-nginx",
                config=CONFIG,
            )

    @patch("cdk8s.ApiObject.to_json")
    def test_cannot_override_default_configmap_data(self, mocked_to_json: Mock) -> None:
        mocked_to_json.return_value = {
            "data": {"foo": "bar"},
        }

        with pytest.raises(LabError, match="ConfigMap is not empty"):
            IngressNginx(
                cdk8s.Testing.app(),
                "ingress-nginx",
                config=CONFIG,
            )