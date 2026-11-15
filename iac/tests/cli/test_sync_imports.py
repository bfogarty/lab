import subprocess
from pathlib import Path
from typing import Any

import pytest
import typer

from lab.cli import sync_imports as sync_module
from lab.cli.sync_imports import STAMP_FILE, sync_imports


class TestSyncImports:
    @pytest.fixture
    def iac_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        iac_dir = tmp_path / "iac"
        iac_dir.mkdir()
        (iac_dir / "cdktf.json").write_text('{"terraformProviders": ["a/b@1"]}')
        (iac_dir / "cdk8s.yaml").write_text("imports: [k8s@1.29.0]")
        monkeypatch.setattr(sync_module, "PROJECT_DIR", iac_dir)
        return iac_dir

    @pytest.fixture
    def run(self, monkeypatch: pytest.MonkeyPatch) -> list[tuple[list[str], Any]]:
        calls: list[tuple[list[str], Any]] = []

        def fake_run(command: list[str], cwd: Path, check: bool) -> None:
            assert check
            calls.append((command, cwd))

        monkeypatch.setattr(sync_module.subprocess, "run", fake_run)
        monkeypatch.setattr(sync_module.shutil, "which", lambda tool: f"/bin/{tool}")
        return calls

    @pytest.fixture
    def output(self, iac_dir: Path) -> Path:
        # Generated into the `lab.imports` package.
        return iac_dir / "lab" / "imports"

    def test_generates_into_the_package_from_the_pins(
        self, iac_dir: Path, run: list, output: Path
    ) -> None:
        sync_imports(force=False)

        assert run == [
            (["cdktf", "get", "--output", str(output)], iac_dir),
            (["cdk8s", "import", "--no-save", "--output", str(output)], iac_dir),
        ]
        assert (output / STAMP_FILE).exists()

    def test_skips_when_pins_are_unchanged(
        self, iac_dir: Path, run: list, output: Path
    ) -> None:
        sync_imports(force=False)
        run.clear()

        sync_imports(force=False)

        assert run == []

    def test_force_regenerates_everything(
        self, iac_dir: Path, run: list, output: Path
    ) -> None:
        sync_imports(force=False)
        run.clear()

        sync_imports(force=True)

        assert [command for command, _ in run] == [
            ["cdktf", "get", "--output", str(output), "--force"],
            ["cdk8s", "import", "--no-save", "--output", str(output)],
        ]

    def test_regenerates_when_a_pin_changes(
        self, iac_dir: Path, run: list, output: Path
    ) -> None:
        sync_imports(force=False)
        run.clear()

        (iac_dir / "cdktf.json").write_text('{"terraformProviders": ["a/b@2"]}')
        sync_imports(force=False)

        assert len(run) == 2

    def test_failed_generation_leaves_no_stamp(
        self,
        iac_dir: Path,
        run: list,
        output: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sync_imports(force=False)

        def failing_run(command: list[str], cwd: Path, check: bool) -> None:
            raise subprocess.CalledProcessError(1, command)

        monkeypatch.setattr(sync_module.subprocess, "run", failing_run)
        with pytest.raises(typer.Exit):
            sync_imports(force=True)

        assert not (output / STAMP_FILE).exists()

    def test_requires_the_clis(
        self,
        iac_dir: Path,
        run: list,
        output: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(sync_module.shutil, "which", lambda tool: None)

        with pytest.raises(typer.Exit):
            sync_imports(force=False)

        assert run == []
