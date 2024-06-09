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
            providers=[
                TerraformModuleProvider(module_alias="home", provider=oci_provider)
            ],
        )
