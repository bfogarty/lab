from enum import StrEnum
from typing import Annotated

from rich import print
import typer
from lab.libs.cli import make_typer

from lab.clusters import BaseCluster, K3sCluster, OkeCluster
from lab.libs.config import parse_config
from lab.libs.exceptions import ConfigError

from cdk8s import App

cli = make_typer()


class ClusterName(StrEnum):
    OKE = "oke"
    K3S = "k3s"


_clusters: dict[ClusterName, type[BaseCluster]] = {
    ClusterName.OKE: OkeCluster,
    ClusterName.K3S: K3sCluster,
}


@cli.command()
def synth(
    config_file: Annotated[typer.FileText, typer.Option()],
    cluster_name: Annotated[ClusterName, typer.Option()],
) -> None:
    cluster_cls = _clusters[cluster_name]
    app = App()

    try:
        config = parse_config(config_file, cluster_cls.config_class)
    except ConfigError as e:
        print(f"[red]{e}[/red]")
        raise typer.Exit(1) from e

    cluster_cls(app, config)

    app.synth()


def register_k8s_cli(app: typer.Typer) -> None:
    app.add_typer(cli, name="k8s")
