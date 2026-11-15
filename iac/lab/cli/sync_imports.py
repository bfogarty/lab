import hashlib
import shutil
import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

import typer
from rich import print

from lab import PROJECT_DIR

GENERATED_PACKAGE_NAME = "imports"

LOCKFILES = ("cdktf.json", "cdk8s.yaml")

STAMP_FILE = ".labcli-imports-digest"


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
            "Run `labcli sync-imports`.[/red]"
        )
        raise typer.Exit(1) from e


def inputs_digest(iac_dir: Path) -> str:
    """
    Hashes the files in `iac_dir` that pin import versions.
    """
    digest = hashlib.sha256()
    for name in LOCKFILES:
        digest.update(name.encode())
        digest.update((iac_dir / name).read_bytes())
    return digest.hexdigest()


def sync_imports(
    output: Annotated[
        Path,
        typer.Option(
            help="Directory to generate the `imports` package into, relative to the "
            "current directory. It must be importable as `imports`."
        ),
    ] = Path("imports"),
    force: Annotated[
        bool,
        typer.Option("--force", help="Regenerate even if the imports look up to date."),
    ] = False,
) -> None:
    """
    Generates or updates the cdktf and cdk8s `imports` package.

    Requires `cdktf` and `cdk8s` on PATH.
    """
    output = output.resolve()
    stamp = output / STAMP_FILE
    digest = inputs_digest(PROJECT_DIR)

    if not force and stamp.exists() and stamp.read_text() == digest:
        print(f"[green]Imports in {output} are up to date.[/green]")
        return

    for tool in ("cdktf", "cdk8s"):
        if shutil.which(tool) is None:
            print(f"[red]`{tool}` not found on PATH.[/red]")
            raise typer.Exit(1)

    # Remove stamp first, so failed/interrupted runs don't look up-to-date.
    output.mkdir(parents=True, exist_ok=True)
    stamp.unlink(missing_ok=True)

    commands = [
        ["cdktf", "get", "--output", str(output)] + (["--force"] if force else []),
        # cdk8s import has no --force. It regenerates every time.
        # --no-save: don't rewrite the pinned imports in cdk8s.yaml.
        ["cdk8s", "import", "--no-save", "--output", str(output)],
    ]
    for command in commands:
        try:
            subprocess.run(command, cwd=PROJECT_DIR, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[red]`{' '.join(command[:2])}` failed (exit {e.returncode}).[/red]")
            raise typer.Exit(1) from e

    stamp.write_text(digest)
    print(f"[green]Generated imports in {output}.[/green]")


def register_sync_imports_cli(app: typer.Typer) -> None:
    app.command("sync-imports")(sync_imports)
