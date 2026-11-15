from lab.cli.infra import register_infra_cli
from lab.cli.k8s import register_k8s_cli
from lab.cli.sync_imports import register_sync_imports_cli

__all__ = [register_infra_cli, register_k8s_cli, register_sync_imports_cli]
