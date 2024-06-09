from lab.cli import register_infra_cli, register_k8s_cli
from lab.libs.cli import make_typer


app = make_typer()

register_infra_cli(app)
register_k8s_cli(app)

if __name__ == "__main__":
    app()
