from cdk8s import ApiObjectMetadata, Chart
from constructs import Construct

from lab.libs.k8s.include import Include

from lab.libs.config import CloudflareAcmeIssuerConfig

from imports.io import cert_manager as cm
import cdk8s_plus_29 as kplus


class CertManager(Chart):
    # must also update CRD version in cdk8s.yaml
    VERSION = "1.18.1"

    NAMESPACE = "cert-manager"

    MANIFEST_URL = f"https://github.com/cert-manager/cert-manager/releases/download/v{VERSION}/cert-manager.yaml"

    def __init__(self, scope: Construct, id_: str):
        super().__init__(scope, id_)

        Include(
            self,
            "cert-manager",
            url=CertManager.MANIFEST_URL,
        )


class CloudflareAcmeIssuer(Chart):
    LETS_ENCRYPT = "https://acme-v02.api.letsencrypt.org/directory"
    LETS_ENCRYPT_STAGING = "https://acme-staging-v02.api.letsencrypt.org/directory"

    API_TOKEN_SECRET_KEY = "api-token"

    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        config: CloudflareAcmeIssuerConfig,
        acme_server: str,
    ):
        super().__init__(scope, id_)

        ##
        ## Secret
        ##
        secret = kplus.Secret(
            self,
            f"{id_}-secret",
            metadata=ApiObjectMetadata(
                namespace=CertManager.NAMESPACE,
            ),
            string_data={
                CloudflareAcmeIssuer.API_TOKEN_SECRET_KEY: config.api_token.get_secret_value()
            },
        )

        ##
        ## ClusterIssuer
        ##
        cloudflare_solver = cm.ClusterIssuerSpecAcmeSolvers(
            dns01=cm.ClusterIssuerSpecAcmeSolversDns01(
                cloudflare=cm.ClusterIssuerSpecAcmeSolversDns01Cloudflare(
                    api_token_secret_ref=cm.ClusterIssuerSpecAcmeSolversDns01CloudflareApiTokenSecretRef(
                        name=secret.name,
                        key=CloudflareAcmeIssuer.API_TOKEN_SECRET_KEY,
                    ),
                ),
            ),
            selector=cm.ClusterIssuerSpecAcmeSolversSelector(
                dns_zones=config.dns_zones,
            ),
        )

        issuer = cm.ClusterIssuer(
            self,
            f"{id_}-cluster-issuer",
            metadata=ApiObjectMetadata(
                namespace=CertManager.NAMESPACE,
            ),
            spec=cm.ClusterIssuerSpec(
                acme=cm.ClusterIssuerSpecAcme(
                    email=config.email,
                    server=acme_server,
                    private_key_secret_ref=cm.ClusterIssuerSpecAcmePrivateKeySecretRef(
                        name=f"{id_}-cluster-issuer-private-key",
                    ),
                    solvers=[cloudflare_solver],
                )
            ),
        )

        self._cluster_issuer_name = issuer.name

    @property
    def cluster_issuer_name(self) -> str:
        return self._cluster_issuer_name
