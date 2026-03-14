from cdk8s import App

from lab.clusters.base import BaseCluster
from lab.charts import (
    Bitwarden,
    CloudflareExternalDns,
    CertManager,
    GrafanaAlloy,
    GrafanaAlloyCrd,
    IngressNginx,
    Tailscale,
    CloudflareAcmeIssuer,
)
from lab.libs.config import OkeClusterConfig


class OkeCluster(BaseCluster):
    config_class = OkeClusterConfig

    def __init__(self, app: App, config: OkeClusterConfig) -> None:
        ##
        ## Cluster Services
        ##
        IngressNginx(app, "ingress-nginx", config.ingress)
        CloudflareExternalDns(
            app, "cloudflare-external-dns", config=config.cloudflare_dns
        )
        CertManager(app, "cert-manager")
        issuer = CloudflareAcmeIssuer(
            app,
            "cloudflare-acme-issuer",
            config=config.cloudflare_acme_issuer,
            acme_server=CloudflareAcmeIssuer.LETS_ENCRYPT,
        )
        GrafanaAlloyCrd(app, "grafana-alloy-crd")
        GrafanaAlloy(app, "grafana-alloy", config=config.grafana)

        ##
        ## Apps
        ##
        Tailscale(app, "tailscale", config=config.tailscale)
        Bitwarden(
            app,
            "bitwarden",
            config=config.bitwarden,
            cluster_issuer_name=issuer.cluster_issuer_name,
            ingress_class_name=IngressNginx.INGRESS_CLASS_NAME,
        )
