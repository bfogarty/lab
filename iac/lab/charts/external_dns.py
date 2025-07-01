from cdk8s import ApiObjectMetadata, Chart
from constructs import Construct
from lab.libs.config import CloudflareDnsConfig

import cdk8s_plus_29 as kplus


class CloudflareExternalDns(Chart):
    VERSION = "0.18.0"

    def __init__(self, scope: Construct, id_: str, *, config: CloudflareDnsConfig):
        super().__init__(scope, id_)

        ns = kplus.Namespace(self, id_)

        ##
        ## Service Account
        ##
        service_account = kplus.ServiceAccount(
            self,
            f"{id_}-service-account",
            metadata=ApiObjectMetadata(namespace=ns.name),
        )

        ##
        ## Cluster Role
        ##
        role = kplus.ClusterRole(
            self,
            f"{id_}-cluster-role",
        )
        role.allow(
            ["get", "watch", "list"],
            kplus.ApiResource.SERVICES,
            kplus.ApiResource.ENDPOINT_SLICES,
            kplus.ApiResource.PODS,
            kplus.ApiResource.INGRESSES,
        )
        role.allow(
            ["watch", "list"],
            kplus.ApiResource.NODES,
        )
        role.bind(service_account)

        ##
        ## Secret
        ##
        secret = kplus.Secret(
            self,
            f"{id_}-secret",
            metadata=ApiObjectMetadata(namespace=ns.name),
            string_data={
                "CF_API_TOKEN": config.api_token.get_secret_value(),
            },
        )

        ##
        ## Deployment
        ##
        kplus.Deployment(
            self,
            f"{id_}-deployment",
            replicas=1,
            service_account=service_account,
            automount_service_account_token=True,
            metadata=ApiObjectMetadata(namespace=ns.name),
        ).add_container(
            image=f"registry.k8s.io/external-dns/external-dns:v{CloudflareExternalDns.VERSION}",
            args=[
                "--source=ingress",
                f"--domain-filter={config.domain}",
                "--provider=cloudflare",
                # helps avoid hitting rate limit on Cloudflare API
                "--cloudflare-dns-records-per-page=5000",
                "--cloudflare-proxied",
                # OCI adds both NLB public, private IPs to the service as external IPs
                f"--exclude-target-net={config.local_network_cidr}",
            ],
            env_from=[
                kplus.EnvFrom(sec=secret),
            ],
            resources=kplus.ContainerResources(
                cpu=None,
                memory=None,
            ),
            security_context=kplus.ContainerSecurityContextProps(
                ensure_non_root=False,
            ),
        )
