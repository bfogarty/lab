import re
from unittest.mock import Mock, patch
import pytest
import cdk8s
from typing import Any, Generator

from lab.charts.grafana import GrafanaAlloy
from lab.libs.config import GrafanaConfig, GrafanaServiceConfig
from pydantic import SecretStr
from tests.utils import get_resource


CONFIG = GrafanaConfig(
    cluster_name="cluster-name",
    access_policy_token=SecretStr("token"),
    loki=GrafanaServiceConfig(host="loki-host", username="loki-username"),
    prometheus=GrafanaServiceConfig(host="prom-host", username="prom-username"),
)


class TestGrafanaAlloy:
    @pytest.fixture(scope="class")
    def chart(self) -> Generator[list[Any], None, None]:
        yield GrafanaAlloy(
            cdk8s.Testing.app(), "grafana-alloy", config=CONFIG
        ).to_json()

    @pytest.fixture
    def mocked_helm(self) -> Generator[Mock, None, None]:
        with patch("lab.charts.grafana.Helm", autospec=True) as m:
            GrafanaAlloy(cdk8s.Testing.app(), "grafana-alloy", config=CONFIG).to_json()

            yield m

    def test_creates_namespace(self, chart: list[Any]) -> None:
        assert get_resource(chart, "Namespace", GrafanaAlloy.NAMESPACE)

    def test_grafana_alloy_deployment(self, chart: list[Any]) -> None:
        # test that we have at least one resource we expect from the Helm chart
        assert get_resource(chart, "Deployment", name=re.compile("grafana-alloy.*"))

    def test_pins_helm_chart_version(self, mocked_helm: Mock) -> None:
        call_kwargs = mocked_helm.call_args.kwargs
        assert "https://grafana.github.io/helm-charts" == call_kwargs["repo"]
        assert "k8s-monitoring" == call_kwargs["chart"]
        assert GrafanaAlloy.CHART_VERSION == call_kwargs["version"]

    def test_helm_resources_are_namespaced(self, chart: list[Any]) -> None:
        assert all(
            x["metadata"]["namespace"] == GrafanaAlloy.NAMESPACE
            for x in chart
            if x["kind"] != "Namespace"
        )

    def test_helm_skip_hooks_and_tests(self, chart: list[Any]) -> None:
        assert all(
            "helm.sh/hook" not in x["metadata"].get("annotations", {}) for x in chart
        )

    def test_cluster_id(self, mocked_helm: Mock) -> None:
        values = mocked_helm.call_args.kwargs["values"]
        assert {"name": CONFIG.cluster_name} == values["cluster"]
        assert {"defaultClusterId": CONFIG.cluster_name} == values["opencost"][
            "opencost"
        ]["exporter"]

    def test_hosts_and_credentials(self, mocked_helm: Mock) -> None:
        values = mocked_helm.call_args.kwargs["values"]

        assert {
            "prometheus": {
                "host": CONFIG.prometheus.host,
                "basicAuth": {
                    "username": CONFIG.prometheus.username,
                    "password": CONFIG.access_policy_token.get_secret_value(),
                },
            },
            "loki": {
                "host": CONFIG.loki.host,
                "basicAuth": {
                    "username": CONFIG.loki.username,
                    "password": CONFIG.access_policy_token.get_secret_value(),
                },
            },
        } == values["externalServices"]

        assert {"external": {"url": f"{CONFIG.prometheus.host}/api/prom"}} == values[
            "opencost"
        ]["opencost"]["prometheus"]

    def test_enabled_features(self, mocked_helm: Mock) -> None:
        values = mocked_helm.call_args.kwargs["values"]

        # metrics
        assert values["metrics"]["enabled"]
        assert values["metrics"]["cost"]["enabled"]
        assert values["metrics"]["node-exporter"]["enabled"]

        # logs
        assert values["logs"]["enabled"]
        assert values["logs"]["pod_logs"]["enabled"]
        assert values["logs"]["cluster_events"]["enabled"]

        # other features
        assert values["opencost"]["enabled"]
        assert values["kube-state-metrics"]["enabled"]
        assert values["prometheus-node-exporter"]["enabled"]
        assert values["prometheus-operator-crds"]["enabled"]

        # traces
        assert not values["traces"]["enabled"]
        assert not values["receivers"]["grpc"]["enabled"]
        assert not values["receivers"]["http"]["enabled"]
        assert not values["receivers"]["zipkin"]["enabled"]
        assert not values["receivers"]["grafanaCloudMetrics"]["enabled"]
