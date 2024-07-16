from typing import Annotated

from rich import print
import typer
from lab.libs.cli import make_typer

from lab.charts import (
    Bitwarden,
    CloudflareExternalDns,
    CertManager,
    IngressNginx,
    Tailscale,
    CloudflareAcmeIssuer,
)
from lab.libs.config import parse_config
from lab.libs.exceptions import ConfigError

from cdk8s import App

cli = make_typer()


@cli.command()
def synth(config_file: Annotated[typer.FileText, typer.Option()]) -> None:
    app = App()

    try:
        config = parse_config(config_file)
    except ConfigError as e:
        print(f"[red]{e}[/red]")
        raise typer.Exit(1) from e

    ##
    ## Cluster Services
    ##
    IngressNginx(app, "ingress-nginx", config.ingress)
    CloudflareExternalDns(app, "cloudflare-external-dns", config=config.cloudflare_dns)
    CertManager(app, "cert-manager")
    issuer = CloudflareAcmeIssuer(
        app,
        "cloudflare-acme-issuer",
        config=config.cloudflare_acme_issuer,
        acme_server=CloudflareAcmeIssuer.LETS_ENCRYPT,
    )

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

    app.synth()


def register_k8s_cli(app: typer.Typer) -> None:
    app.add_typer(cli, name="k8s")
