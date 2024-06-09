import typer
from lab.libs.cli import make_typer

from cdk8s import App

cli = make_typer()


@cli.command()
def synth() -> None:
    app = App()

    app.synth()


def register_k8s_cli(app: typer.Typer) -> None:
    app.add_typer(cli, name="k8s")
