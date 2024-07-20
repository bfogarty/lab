import re
from collections.abc import Generator
from ipaddress import IPv4Network
from typing import Any
from lab.charts.external_dns import CloudflareExternalDns
from pydantic import SecretStr
import pytest
import cdk8s

import cdk8s_plus_29 as kplus

from lab.libs.config import CloudflareDnsConfig
from tests.utils import get_resource


CF_DOMAIN = "example.com"
CF_API_TOKEN = "token"
VCN_CIDR = IPv4Network("10.0.0.0/16")

RESOURCE_NAME_PATTERN = re.compile(".*cloudflare-external-dns.*")


class TestCloudflareExternalDns:
    @pytest.fixture(scope="class")
    def chart(self) -> Generator[list[Any], None, None]:
        yield CloudflareExternalDns(
            cdk8s.Testing.app(),
            "cloudflare-external-dns",
            config=CloudflareDnsConfig(
                domain=CF_DOMAIN,
                api_token=SecretStr(CF_API_TOKEN),
                local_network_cidr=VCN_CIDR,
            ),
        ).to_json()

    @pytest.fixture(scope="class")
    def container(self, chart: list[Any]) -> Generator[dict[str, Any], None, None]:
        deploy = get_resource(chart, "Deployment", RESOURCE_NAME_PATTERN)
        yield deploy["spec"]["template"]["spec"]["containers"][0]

    def test_creates_namespace(self, chart: list[Any]) -> None:
        assert get_resource(chart, "Namespace", RESOURCE_NAME_PATTERN)

    def test_creates_service_account(self, chart: list[Any]) -> None:
        assert get_resource(
            chart,
            "ServiceAccount",
            RESOURCE_NAME_PATTERN,
        )

    @pytest.mark.parametrize(
        "resource",
        [
            kplus.ApiResource.SERVICES,
            kplus.ApiResource.ENDPOINTS,
            kplus.ApiResource.PODS,
            kplus.ApiResource.INGRESSES,
        ],
        ids=lambda x: x.resource_type,
    )
    def test_cluster_role_permissions(
        self, chart: list[Any], resource: kplus.ApiResource
    ) -> None:
        role = get_resource(
            chart,
            "ClusterRole",
            RESOURCE_NAME_PATTERN,
        )

        assert {
            "apiGroups": [resource.api_group],
            "resourceNames": [],
            "resources": [resource.resource_type],
            "verbs": ["get", "watch", "list"],
        } in role["rules"]

    def test_cluster_role_node_permissions(self, chart: list[Any]) -> None:
        role = get_resource(
            chart,
            "ClusterRole",
            RESOURCE_NAME_PATTERN,
        )

        assert {
            "apiGroups": [kplus.ApiResource.NODES.api_group],
            "resourceNames": [],
            "resources": [kplus.ApiResource.NODES.resource_type],
            "verbs": ["watch", "list"],
        } in role["rules"]

    def test_cluster_role_binding(self, chart: list[Any]) -> None:
        crb = get_resource(
            chart,
            "ClusterRoleBinding",
            RESOURCE_NAME_PATTERN,
        )
        cr = get_resource(
            chart,
            "ClusterRole",
            RESOURCE_NAME_PATTERN,
        )
        sa = get_resource(
            chart,
            "ServiceAccount",
            RESOURCE_NAME_PATTERN,
        )

        assert {"kind": "ClusterRole", "name": cr["metadata"]["name"]}.items() <= crb[
            "roleRef"
        ].items()

        assert {
            "apiGroup": "",
            "kind": "ServiceAccount",
            "name": sa["metadata"]["name"],
            "namespace": sa["metadata"]["namespace"],
        } in crb["subjects"]

    def test_secret(self, chart: list[Any]) -> None:
        secret = get_resource(
            chart,
            "Secret",
            RESOURCE_NAME_PATTERN,
        )

        assert {"CF_API_TOKEN": CF_API_TOKEN} == secret["stringData"]

    def test_deployment_service_account(self, chart: list[Any]) -> None:
        deploy = get_resource(chart, "Deployment", RESOURCE_NAME_PATTERN)
        sa = get_resource(chart, "ServiceAccount", RESOURCE_NAME_PATTERN)
        assert deploy["spec"]["template"]["spec"]["automountServiceAccountToken"]
        assert (
            sa["metadata"]["name"]
            == deploy["spec"]["template"]["spec"]["serviceAccountName"]
        )

    def test_deployment_image(self, container: dict[str, Any]) -> None:
        assert (
            f"registry.k8s.io/external-dns/external-dns:v{CloudflareExternalDns.VERSION}"
            == container["image"]
        )

    def test_deployment_env(self, chart: list[Any], container: dict[str, Any]) -> None:
        secret = get_resource(chart, "Secret", RESOURCE_NAME_PATTERN)
        assert [{"secretRef": {"name": secret["metadata"]["name"]}}] == container[
            "envFrom"
        ]

    def test_deployment_args(self, container: dict[str, Any]) -> None:
        assert [
            "--source=ingress",
            f"--domain-filter={CF_DOMAIN}",
            "--provider=cloudflare",
            "--cloudflare-dns-records-per-page=5000",
            "--cloudflare-proxied",
            f"--exclude-target-net={VCN_CIDR}",
        ] == container["args"]

    def test_resources(self, container: dict[str, Any]) -> None:
        assert "resources" not in container

    def test_security_context(self, container: dict[str, Any]) -> None:
        assert not container["securityContext"]["runAsNonRoot"]
