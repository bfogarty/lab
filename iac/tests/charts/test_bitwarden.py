import re
from collections.abc import Generator
from typing import Any
from lab.charts.bitwarden import Bitwarden
from pydantic import SecretStr
import pytest
import cdk8s


from lab.libs.config import BitwardenConfig, BitwardenSmtpConfig
from tests.utils import get_resource

import cdk8s_plus_29 as kplus


CONFIG = BitwardenConfig(
    admin_token=SecretStr("bw-example-token"),
    domain="https://example.com",
    organization_name="Example Org",
    icon_blacklist_regex=r"example\.com",
    smtp=BitwardenSmtpConfig(
        host="smtp.example.com",
        port=587,
        username="admin",
        password=SecretStr("example-smtp-pass"),
        from_email="admin@example.com",
        from_name="Example Org",
        use_explicit_tls=True,
    ),
)

RESOURCE_NAME_PATTERN = re.compile(".*bitwarden.*")

INGRESS_CLASS_NAME = "nginx"
CLUSTER_ISSUER_NAME = "cluster-issuer"


class TestBitwarden:
    @pytest.fixture(scope="class")
    def chart(self) -> Generator[list[Any], None, None]:
        yield Bitwarden(
            cdk8s.Testing.app(),
            "bitwarden",
            config=CONFIG,
            ingress_class_name=INGRESS_CLASS_NAME,
            cluster_issuer_name=CLUSTER_ISSUER_NAME,
        ).to_json()

    @pytest.fixture(scope="class")
    def container(self, chart: list[Any]) -> Generator[dict[str, Any], None, None]:
        deploy = get_resource(chart, "Deployment", RESOURCE_NAME_PATTERN)
        yield deploy["spec"]["template"]["spec"]["containers"][0]

    @pytest.fixture(scope="class")
    def ingress(self, chart: list[Any]) -> Generator[dict[str, Any], None, None]:
        yield get_resource(chart, "Ingress", RESOURCE_NAME_PATTERN)

    def test_creates_namespace(self, chart: list[Any]) -> None:
        assert get_resource(chart, "Namespace", "bitwarden")

    def test_configmap(self, chart: list[Any]) -> None:
        cm = get_resource(chart, "ConfigMap", RESOURCE_NAME_PATTERN)
        assert {
            "DOMAIN": CONFIG.domain,
            "ICON_BLACKLIST_REGEX": CONFIG.icon_blacklist_regex,
            "INVITATION_ORG_NAME": CONFIG.organization_name,
            "SHOW_PASSWORD_HINT": "false",
            "SIGNUPS_ALLOWED": "false",
            "SMTP_EXPLICIT_TLS": "true" if CONFIG.smtp.use_explicit_tls else "false",
            "SMTP_FROM": CONFIG.smtp.from_email,
            "SMTP_FROM_NAME": CONFIG.smtp.from_name,
            "SMTP_HOST": CONFIG.smtp.host,
            "SMTP_PORT": str(CONFIG.smtp.port),
            "SMTP_USERNAME": CONFIG.smtp.username,
        } == cm["data"]

    def test_secret(self, chart: list[Any]) -> None:
        secret = get_resource(chart, "Secret", RESOURCE_NAME_PATTERN)
        assert {
            "ADMIN_TOKEN": CONFIG.admin_token.get_secret_value(),
            "SMTP_PASSWORD": CONFIG.smtp.password.get_secret_value(),
        } == secret["stringData"]

    def test_pvc(self, chart: list[Any]) -> None:
        pvc = get_resource(chart, "PersistentVolumeClaim", RESOURCE_NAME_PATTERN)
        assert "15Gi" == pvc["spec"]["resources"]["requests"]["storage"]
        assert ["ReadWriteOncePod"] == pvc["spec"]["accessModes"]

    def test_deployment_image(self, container: dict[str, Any]) -> None:
        assert f"vaultwarden/server:{Bitwarden.VERSION}" == container["image"]

    def test_deployment_env(self, chart: list[Any], container: dict[str, Any]) -> None:
        secret = get_resource(chart, "Secret", RESOURCE_NAME_PATTERN)
        cm = get_resource(chart, "ConfigMap", RESOURCE_NAME_PATTERN)

        assert 2 == len(container["envFrom"])
        assert {"secretRef": {"name": secret["metadata"]["name"]}} in container[
            "envFrom"
        ]
        assert {"configMapRef": {"name": cm["metadata"]["name"]}} in container[
            "envFrom"
        ]

    def test_port(self, container: dict[str, Any]) -> None:
        assert [
            {
                "containerPort": 80,
                "name": "http",
            }
        ] == container["ports"]

    def test_probes(self, container: dict[str, Any]) -> None:
        expected_probe = {"httpGet": {"path": "/", "port": 80, "scheme": "HTTP"}}

        assert expected_probe.items() <= container["livenessProbe"].items()
        assert expected_probe.items() <= container["readinessProbe"].items()

    def test_resources(self, container: dict[str, Any]) -> None:
        assert "resources" not in container

    def test_security_context(self, container: dict[str, Any]) -> None:
        assert not container["securityContext"]["runAsNonRoot"]

    def test_volume_mounts(self, chart: list[Any], container: dict[str, Any]) -> None:
        pvc = get_resource(chart, "PersistentVolumeClaim", RESOURCE_NAME_PATTERN)
        deploy = get_resource(chart, "Deployment", RESOURCE_NAME_PATTERN)

        assert 1 == len(deploy["spec"]["template"]["spec"]["volumes"])
        volume = deploy["spec"]["template"]["spec"]["volumes"][0]

        assert {
            "persistentVolumeClaim": {
                "claimName": pvc["metadata"]["name"],
                "readOnly": False,
            }
        }.items() <= volume.items()

        assert [
            {
                "name": volume["name"],
                "mountPath": "/data",
            }
        ] == container["volumeMounts"]

    def test_ingress_tls_enabled(
        self, chart: list[Any], ingress: dict[str, Any]
    ) -> None:
        tls_secret = get_resource(chart, "Secret", re.compile(".*bitwarden-tls.*"))

        assert {
            "cert-manager.io/cluster-issuer": CLUSTER_ISSUER_NAME,
        }.items() <= ingress["metadata"]["annotations"].items()

        hostname = CONFIG.domain.replace("https://", "")
        assert [
            {"hosts": [hostname], "secretName": tls_secret["metadata"]["name"]}
        ] == ingress["spec"]["tls"]

    def test_ingress_admin_deny_all(self, ingress: dict[str, Any]) -> None:
        assert {
            "nginx.ingress.kubernetes.io/server-snippet": "location /admin { deny all; }"
        }.items() <= ingress["metadata"]["annotations"].items()

    def test_ingress_classs(self, ingress: dict[str, Any]) -> None:
        assert INGRESS_CLASS_NAME == ingress["spec"]["ingressClassName"]

    def test_ingress_rules(self, chart: list[Any], ingress: dict[str, Any]) -> None:
        service = get_resource(chart, "Service", RESOURCE_NAME_PATTERN)

        assert 1 == len(service["spec"]["ports"])
        port = service["spec"]["ports"][0]["port"]

        hostname = CONFIG.domain.replace("https://", "")
        assert [
            {
                "host": hostname,
                "http": {
                    "paths": [
                        {
                            "backend": {
                                "service": {
                                    "name": service["metadata"]["name"],
                                    "port": {"number": port},
                                }
                            },
                            "path": "/",
                            "pathType": "Prefix",
                        }
                    ]
                },
            }
        ] == ingress["spec"]["rules"]

    def test_service_type(self, chart: list[Any], container: dict[str, Any]) -> None:
        service = get_resource(chart, "Service", RESOURCE_NAME_PATTERN)
        assert "ClusterIP" == service["spec"]["type"]

    def test_service_ports(self, chart: list[Any], container: dict[str, Any]) -> None:
        service = get_resource(chart, "Service", RESOURCE_NAME_PATTERN)

        container_ports = sorted(x["containerPort"] for x in container["ports"])
        service_target_ports = sorted(x["targetPort"] for x in service["spec"]["ports"])
        service_ports =  sorted(x["port"] for x in service["spec"]["ports"])

        # each container port is targeted, and only once
        assert container_ports == service_target_ports

        # no duplicate service ports
        assert len(service_ports) == len(set(service_ports))
