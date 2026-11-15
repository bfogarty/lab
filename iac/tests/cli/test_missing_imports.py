import subprocess
import sys

import pytest
import typer

from lab.cli.sync_imports import missing_imports_hint

# Run in a subprocess with the generated package blocked.
BLOCK_IMPORTS = "import sys; sys.modules['imports'] = None; "


def run_without_imports(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", BLOCK_IMPORTS + code],
        capture_output=True,
        text=True,
    )


class TestMissingImportsHint:
    def test_turns_a_missing_imports_package_into_an_exit(self) -> None:
        with pytest.raises(typer.Exit):
            with missing_imports_hint():
                raise ModuleNotFoundError("No module named 'imports'", name="imports")

    def test_covers_submodules_of_imports(self) -> None:
        with pytest.raises(typer.Exit):
            with missing_imports_hint():
                raise ModuleNotFoundError(
                    "No module named 'imports.oci'", name="imports.oci"
                )

    def test_leaves_other_missing_modules_alone(self) -> None:
        with pytest.raises(ModuleNotFoundError):
            with missing_imports_hint():
                raise ModuleNotFoundError("No module named 'foo'", name="foo")


class TestLabcliWithoutImports:
    def test_starts(self) -> None:
        result = run_without_imports("import lab.__main__")

        assert result.returncode == 0, result.stderr

    @pytest.mark.parametrize(
        "call",
        [
            "from lab.cli.k8s import ClusterName, synth; "
            "import io; "
            "synth(config_file=io.StringIO(''), cluster_name=ClusterName.OKE)",
            "from lab.cli.infra import synth; "
            "synth(tfc_organization='org', tfc_workspace='lab')",
        ],
    )
    def test_synth_says_how_to_generate_the_imports(self, call: str) -> None:
        result = run_without_imports(
            f"import typer\ntry:\n    {call}\nexcept typer.Exit as e:\n"
            "    print('exit', e.exit_code)"
        )

        assert result.returncode == 0, result.stderr
        # The message wraps to the terminal width.
        output = " ".join(result.stdout.split())
        assert "exit 1" in output
        assert "labcli sync-imports" in output


def test_sync_imports_is_a_labcli_command() -> None:
    from lab.__main__ import app

    assert "sync-imports" in [command.name for command in app.registered_commands]
