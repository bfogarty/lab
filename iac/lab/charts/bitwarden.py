from constructs import Construct

from cdk8s import ApiObjectMetadata, Chart, Size

import cdk8s_plus_29 as kplus
from lab.libs.config import BitwardenConfig


class Bitwarden(Chart):
    VERSION = "1.32.4"

    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        config: BitwardenConfig,
        ingress_class_name: str,
        cluster_issuer_name: str,
    ):
        super().__init__(scope, id_, namespace="bitwarden")

        ##
        ## Namespace
        ##
        kplus.Namespace(self, f"{id_}-ns", metadata=ApiObjectMetadata(name="bitwarden"))

        ##
        ## Secret + ConfigMap
        ##
        secret = kplus.Secret(
            self,
            f"{id_}-secret",
            string_data={
                "ADMIN_TOKEN": config.admin_token.get_secret_value(),
                "SMTP_PASSWORD": config.smtp.password.get_secret_value(),
            },
        )

        configmap = kplus.ConfigMap(
            self,
            f"{id_}-configmap",
            data={
                "DOMAIN": config.domain,
                "SIGNUPS_ALLOWED": "false",
                "SHOW_PASSWORD_HINT": "false",
                "INVITATION_ORG_NAME": config.organization_name,
                "ICON_BLACKLIST_REGEX": config.icon_blacklist_regex,
                "SMTP_HOST": config.smtp.host,
                "SMTP_FROM": config.smtp.from_email,
                "SMTP_FROM_NAME": config.smtp.from_name,
                "SMTP_PORT": str(config.smtp.port),
                "SMTP_EXPLICIT_TLS": str(config.smtp.use_explicit_tls).lower(),
                "SMTP_USERNAME": config.smtp.username,
            },
        )

        ##
        ## PVC
        ##
        claim = kplus.PersistentVolumeClaim(
            self,
            f"{id_}-pvc",
            access_modes=[kplus.PersistentVolumeAccessMode.READ_WRITE_ONCE_POD],
            storage=Size.gibibytes(15),
        )

        ##
        ## Deployment
        ##
        deployment = kplus.Deployment(
            self,
            id_,
            replicas=1,
        )

        main_container = deployment.add_container(
            image=f"vaultwarden/server:{Bitwarden.VERSION}",
            resources=kplus.ContainerResources(
                cpu=None,
                memory=None,
            ),
            env_from=[kplus.EnvFrom(config_map=configmap), kplus.EnvFrom(sec=secret)],
            ports=[
                kplus.ContainerPort(name="http", number=80),
            ],
            liveness=kplus.Probe.from_http_get(path="/"),
            readiness=kplus.Probe.from_http_get(path="/"),
            security_context=kplus.ContainerSecurityContextProps(
                ensure_non_root=False,
            ),
        )

        main_container.mount(
            "/data",
            kplus.Volume.from_persistent_volume_claim(
                self, f"{id_}-data-volume", claim=claim
            ),
        )

        ##
        ## Ingress
        ##
        ing = kplus.Ingress(self, f"{id_}-ingress", class_name=ingress_class_name)
        host = config.domain.replace("https://", "")
        ing.add_host_rule(
            host=host,
            path="/",
            backend=kplus.IngressBackend.from_service(deployment.expose_via_service()),
        )
        ing.metadata.add_annotation(
            "cert-manager.io/cluster-issuer",
            cluster_issuer_name,
        )
        ing.metadata.add_annotation(
            "nginx.ingress.kubernetes.io/server-snippet",
            "location /admin { deny all; }",
        )
        ing.add_tls(
            [kplus.IngressTls(hosts=[host], secret=kplus.Secret(self, f"{id_}-tls"))]
        )
