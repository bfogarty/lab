from ipaddress import IPv4Network

import cdk8s
from pydantic import SecretStr

from lab.clusters.oke import OkeCluster
from lab.libs.config import (
    BitwardenConfig,
    BitwardenSmtpConfig,
    CloudflareAcmeIssuerConfig,
    CloudflareDnsConfig,
    GrafanaConfig,
    GrafanaServiceConfig,
    IngressConfig,
    OkeClusterConfig,
    TailscaleConfig,
)


CONFIG = OkeClusterConfig(
    bitwarden=BitwardenConfig(
        admin_token=SecretStr("bw-token"),
        domain="https://example.com",
        organization_name="Example Org",
        smtp=BitwardenSmtpConfig(
            host="smtp.example.com",
            port=587,
            username="admin",
            password=SecretStr("smtp-pass"),
            from_email="admin@example.com",
            from_name="Example Org",
            security="force_tls",
        ),
    ),
    tailscale=TailscaleConfig(
        client_id="client-id",
        client_secret=SecretStr("client-secret"),
    ),
    cloudflare_acme_issuer=CloudflareAcmeIssuerConfig(
        email="admin@example.com",
        api_token=SecretStr("cf-token"),
        dns_zones=["example.com"],
    ),
    cloudflare_dns=CloudflareDnsConfig(
        domain="example.com",
        api_token=SecretStr("cf-dns-token"),
        local_network_cidr=IPv4Network("10.0.0.0/16"),
    ),
    grafana=GrafanaConfig(
        cluster_name="test-cluster",
        access_policy_token=SecretStr("grafana-token"),
        loki=GrafanaServiceConfig(host="loki-host", username="loki-user"),
        prometheus=GrafanaServiceConfig(host="prom-host", username="prom-user"),
        remote_config=GrafanaServiceConfig(host="fleet-host", username="fleet-user"),
    ),
    ingress=IngressConfig(
        oci_public_load_balancer_nsg_ocid="ocid",
    ),
)


class TestOkeCluster:
    def test_initializes_without_error(self) -> None:
        app = cdk8s.Testing.app()
        OkeCluster(app, CONFIG)
