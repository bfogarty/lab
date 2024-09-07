from typing import Annotated

from rich import print
import typer
from lab.libs.cli import make_typer

from lab.charts import IngressNginx, Tailscale
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

    ##
    ## Apps
    ##
    Tailscale(app, "tailscale", config=config.tailscale)

    app.synth()


def register_k8s_cli(app: typer.Typer) -> None:
    app.add_typer(cli, name="k8s")
