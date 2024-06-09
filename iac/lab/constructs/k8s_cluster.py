from cdktf import TerraformModuleProvider

from constructs import Construct

from imports.oke import Oke
from imports.oci.provider import OciProvider


class KubernetesCluster(Construct):
    VERSION = "v1.29.1"

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

        Oke(
            self,
            f"cluster-{name}",
            cluster_name=name,
            kubernetes_version=KubernetesCluster.VERSION,
            tenancy_id=tenancy_id,
            compartment_id=compartment_id,
            control_plane_is_public=True,
            assign_public_ip_to_control_plane=True,
            create_bastion=False,
            create_operator=False,
            # workaround: module should disable operator subnet, but doesn't
            subnets={
                "bastion": {"newbits": 13},
                "operator": {"create": "never"},
                "cp": {"newbits": 13},
                "int_lb": {"newbits": 11},
                "pub_lb": {"newbits": 11},
                "workers": {"newbits": 4},
                "pods": {"newbits": 2},
            },
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
            providers=[
                TerraformModuleProvider(module_alias="home", provider=oci_provider)
            ],
        )
