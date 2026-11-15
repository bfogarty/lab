from collections.abc import Generator
from contextlib import contextmanager

import typer
from rich import print

GENERATED_PACKAGE_NAME = "imports"


@contextmanager
def missing_imports_hint() -> Generator[None]:
    """
    Wraps imports to the generated `imports` packages and prints on error.
    """
    try:
        yield
    except ModuleNotFoundError as e:
        if (e.name or "").split(".")[0] != GENERATED_PACKAGE_NAME:
            raise
        print(
            f"[red]The generated `{GENERATED_PACKAGE_NAME}` package is missing. "
            "Run `cdktf get` and `cdk8s import`.[/red]"
        )
        raise typer.Exit(1) from e
