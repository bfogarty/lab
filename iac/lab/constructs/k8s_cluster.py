from cdktf import TerraformModuleProvider

from constructs import Construct

from imports.oke import Oke
from imports.oci.provider import OciProvider


class KubernetesCluster(Construct):
    CONTROL_PLANE_VERSION = "v1.30.10"
    WORKER_NODE_VERSION = "v1.30.10"

    # control upgrades to workers by pinning the image
    PINNED_WORKER_IMAGE = "ocid1.image.oc1.iad.aaaaaaaalyoeitqqpnuh5amzx7sfcw7ffz4m2xmmvqysnvjoekm676pmbbyq"

    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        name: str,
        oci_provider: OciProvider,
        tenancy_id: str,
        compartment_id: str,
    ):
        super().__init__(scope, id_)

        public_load_balancer_rules = {
            "Allow TCP ingress to public load balancers for HTTPS traffic from anywhere": {
                "protocol": 6,
                "port": 443,
                "source": "0.0.0.0/0",
                "source_type": "CIDR_BLOCK",
            },
            "Allow TCP ingress to public load balancers for HTTP traffic from anywhere": {
                "protocol": 6,
                "port": 80,
                "source": "0.0.0.0/0",
                "source_type": "CIDR_BLOCK",
            },
        }

        Oke(
            self,
            f"cluster-{name}",
            cluster_name=name,
            kubernetes_version=KubernetesCluster.CONTROL_PLANE_VERSION,
            tenancy_id=tenancy_id,
            compartment_id=compartment_id,
            control_plane_is_public=True,
            create_bastion=False,
            create_operator=False,
            worker_pools={
                "default": {
                    "mode": "node-pool",
                    "size": 2,
                    "shape": "VM.Standard.A1.Flex",
                    "ocpus": 2,
                    "memory": 12,
                    "boot_volume_size": 50,
                    "kubernetes_version": KubernetesCluster.WORKER_NODE_VERSION,
                },
            },
            allow_rules_public_lb=public_load_balancer_rules,
            worker_image_type="custom",
            worker_image_id=KubernetesCluster.PINNED_WORKER_IMAGE,
            providers=[
                TerraformModuleProvider(module_alias="home", provider=oci_provider)
            ],
            # bug in module version >= 5.1.1: when disabling operator, subnets
            # and security groups are still created. here we override the
            # operator to create = "never" while keeping defaults for the rest
            nsgs={
              "bastion": {},
              "operator": {"create": "never"},
              "cp": {},
              "int_lb": {},
              "pub_lb": {},
              "workers": {},
              "pods": {},
            },
            subnets={
                "bastion": { "newbits": 13, "ipv6_cidr": "8, 0" },
                "operator": { "create": "never" },
                "cp": { "newbits": 13, "ipv6_cidr": "8, 2" },
                "int_lb": { "newbits": 11, "ipv6_cidr": "8, 3" },
                "pub_lb": { "newbits": 11, "ipv6_cidr": "8, 4" },
                "workers": { "newbits": 4, "ipv6_cidr": "8, 5" },
                "pods": { "newbits": 2, "ipv6_cidr": "8, 6" },
            },
        )
