import typer


def make_typer() -> typer.Typer:
    return typer.Typer(no_args_is_help=True)


def make_envvar(name: str) -> str:
    return f"LAB_{name}"
