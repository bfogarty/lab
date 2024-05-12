from typing import Annotated
import typer

from cdktf import App, CloudBackend, NamedCloudWorkspace

from lab.stacks import Lab


cli = typer.Typer(no_args_is_help=True)


def make_envvar(name: str) -> str:
    return f"LAB_{name}"


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

    CloudBackend(
        app,
        organization=tfc_organization,
        workspaces=NamedCloudWorkspace(tfc_workspace),
    )

    Lab(app, "lab")

    app.synth()


@cli.callback()
def callback():
    pass


if __name__ == "__main__":
    cli()
