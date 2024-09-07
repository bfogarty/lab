from cdktf import TerraformModuleProvider

from constructs import Construct

from imports.oke import Oke
from imports.oci.provider import OciProvider


class KubernetesCluster(Construct):
    VERSION = "v1.29.1"

    # control upgrades to workers by pinning the image
    PINNED_WORKER_IMAGE = "ocid1.image.oc1.iad.aaaaaaaahlop3h45zzpfcjdrmzqg3yebrnsdrblicwyr57jb4o7f6pxhu7dq"

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

        # module pinned below < 5.1.1 to work around bug disabling operator
        # where subnets and security groups are still created
        Oke(
            self,
            f"cluster-{name}",
            cluster_name=name,
            kubernetes_version=KubernetesCluster.VERSION,
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
                },
            },
            allow_rules_public_lb=public_load_balancer_rules,
            worker_image_type="custom",
            worker_image_id=KubernetesCluster.PINNED_WORKER_IMAGE,
            providers=[
                TerraformModuleProvider(module_alias="home", provider=oci_provider)
            ],
        )
