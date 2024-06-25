from collections.abc import Generator
import re
from typing import Any
import pytest
import cdk8s

from lab.charts.tailscale import Tailscale
from lab.libs.config import TailscaleClusterApiProxy, TailscaleConfig
from tests.utils import get_resource
from pydantic import SecretStr

from tests.utils import get_default_container_env

CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
ADMIN_USER = "test@test.com"


def _get_api_server_proxy_status(deployment: Any) -> str:
    try:
        return next(
            x
            for x in get_default_container_env(deployment)
            if x.get("name") == "APISERVER_PROXY"
        ).get("value", "")
    except StopIteration:
        pytest.fail("env var 'APISERVER_PROXY' not found")


class TestTailscaleDefault:
    @pytest.fixture(scope="class")
    def chart(self) -> Generator[list[Any], None, None]:
        yield Tailscale(
            cdk8s.Testing.app(),
            "tailscale",
            config=TailscaleConfig(
                client_id=CLIENT_ID,
                client_secret=SecretStr(CLIENT_SECRET),
            ),
        ).to_json()

    def test_includes_operator_manifest(self, chart: list[Any]) -> None:
        assert get_resource(chart, "Deployment", "operator")

    def test_oauth_secret(self, chart: list[Any]) -> None:
        secret = get_resource(chart, "Secret", "operator-oauth")
        assert CLIENT_ID == secret["stringData"]["client_id"]
        assert CLIENT_SECRET == secret["stringData"]["client_secret"]

    def test_default_api_proxy_disabled(self, chart: list[Any]) -> None:
        deployment = get_resource(chart, "Deployment", "operator")
        assert "false" == _get_api_server_proxy_status(deployment)

    def test_default_no_api_proxy_rbac(self, chart: list[Any]) -> None:
        with pytest.raises(StopIteration):
            get_resource(chart, "ClusterRoleBinding", "tailscale-auth-proxy")


class TestTailscaleApiProxyEnabled:
    @pytest.fixture(scope="class")
    def chart(self) -> Generator[list[Any], None, None]:
        yield Tailscale(
            cdk8s.Testing.chart(),
            "tailscale",
            config=TailscaleConfig(
                client_id=CLIENT_ID,
                client_secret=SecretStr(CLIENT_SECRET),
                cluster_api_proxy=TailscaleClusterApiProxy(
                    cluster_admins=[ADMIN_USER],
                ),
            ),
        ).to_json()

    def test_api_proxy_enabled(self, chart: list[Any]) -> None:
        deployment = get_resource(chart, "Deployment", "operator")
        assert "true" == _get_api_server_proxy_status(deployment)

    def test_api_proxy_rbac(self, chart: list[Any]) -> None:
        assert get_resource(chart, "ClusterRoleBinding", "tailscale-auth-proxy")

    def test_api_proxy_clusterrolebinding(self, chart: list[Any]) -> None:
        cluster_admins = get_resource(
            chart,
            "ClusterRoleBinding",
            re.compile(".*tailscale-cluster-admins.*"),
        )

        assert cluster_admins
        assert 1 == len(cluster_admins["subjects"])
        assert {
            "kind": "User",
            "name": ADMIN_USER,
        }.items() <= cluster_admins["subjects"][0].items()
        assert {
            "kind": "ClusterRole",
            "name": "cluster-admin",
        }.items() <= cluster_admins["roleRef"].items()
