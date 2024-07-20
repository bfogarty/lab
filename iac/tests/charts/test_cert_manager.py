import re
from collections.abc import Generator
from typing import Any
from lab.charts.cert_manager import CertManager, CloudflareAcmeIssuer
from pydantic import SecretStr
import pytest
import cdk8s


from lab.libs.config import CloudflareAcmeIssuerConfig
from tests.utils import get_resource


EMAIL = "admin@example.com"
API_TOKEN = "cf-example-token"
DNS_ZONE = "example.com"

CHART_NAME = "cloudflare-acme-issuer"

RESOURCE_NAME_PATTERN = re.compile(".*cloudflare-acme-issuer.*")


class TestCertManager:
    def test_cert_manager_include(self) -> None:
        cm = CertManager(cdk8s.Testing.app(), "cert-manager").to_json()
        assert get_resource(cm, "Deployment", "cert-manager")


class TestCloudflareAcmeIssuer:
    @pytest.fixture
    def chart(self) -> Generator[CloudflareAcmeIssuer, None, None]:
        yield CloudflareAcmeIssuer(
            cdk8s.Testing.app(),
            CHART_NAME,
            config=CloudflareAcmeIssuerConfig(
                email=EMAIL,
                api_token=SecretStr(API_TOKEN),
                dns_zones=[DNS_ZONE],
            ),
            acme_server=CloudflareAcmeIssuer.LETS_ENCRYPT_STAGING,
        )

    @pytest.fixture
    def secret(
        self, chart: CloudflareAcmeIssuer
    ) -> Generator[dict[str, Any], None, None]:
        yield get_resource(chart.to_json(), "Secret", RESOURCE_NAME_PATTERN)

    @pytest.fixture
    def issuer(
        self,
        chart: CloudflareAcmeIssuer,
    ) -> Generator[dict[str, Any], None, None]:
        yield get_resource(chart.to_json(), "ClusterIssuer", RESOURCE_NAME_PATTERN)

    def test_secret(self, secret: dict[str, Any]) -> None:
        assert {CloudflareAcmeIssuer.API_TOKEN_SECRET_KEY: API_TOKEN} == secret[
            "stringData"
        ]

    def test_issuer_private_key_secret(self, issuer: dict[str, Any]) -> None:
        assert {"name": f"{CHART_NAME}-cluster-issuer-private-key"} == issuer["spec"][
            "acme"
        ]["privateKeySecretRef"]

    def test_issuer_email(self, issuer: dict[str, Any]) -> None:
        assert EMAIL == issuer["spec"]["acme"]["email"]

    def test_issuer_server(self, issuer: dict[str, Any]) -> None:
        assert (
            CloudflareAcmeIssuer.LETS_ENCRYPT_STAGING
            == issuer["spec"]["acme"]["server"]
        )

    def test_issuer_solvers(
        self, secret: dict[str, Any], issuer: dict[str, Any]
    ) -> None:
        assert [
            {
                "dns01": {
                    "cloudflare": {
                        "apiTokenSecretRef": {
                            "key": CloudflareAcmeIssuer.API_TOKEN_SECRET_KEY,
                            "name": secret["metadata"]["name"],
                        },
                    }
                },
                "selector": {
                    "dnsZones": [DNS_ZONE],
                },
            }
        ] == issuer["spec"]["acme"]["solvers"]

    def test_cluster_issuer_name_property(
        self, chart: CloudflareAcmeIssuer, issuer: dict[str, Any]
    ) -> None:
        assert issuer["metadata"]["name"] == chart.cluster_issuer_name
