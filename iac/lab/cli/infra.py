from typing import Annotated
import typer

from cdktf import App, CloudBackend, NamedCloudWorkspace

from lab.stacks import Lab
from lab.libs.cli import make_typer, make_envvar

cli = make_typer()


@cli.command()
def synth(
    tfc_organization: Annotated[
        str,
        typer.Option(
            envvar=make_envvar("TFC_ORGANIZATION"), help="Terraform Cloud organization"
        ),
    ],
    tfc_workspace: Annotated[
        str,
        typer.Option(
            envvar=make_envvar("TFC_WORKSPACE"), help="Terraform Cloud workspace"
        ),
    ] = "lab",
) -> None:
    """
    Synthesizes this project to Terraform.
    """
    app = App()

    stacks = [Lab(app, "lab")]

    for s in stacks:
        CloudBackend(
            s,
            organization=tfc_organization,
            workspaces=NamedCloudWorkspace(tfc_workspace),
        )

    app.synth()


def register_infra_cli(app: typer.Typer) -> None:
    app.add_typer(cli, name="infra")
