from constructs import Construct
from cdktf import TerraformModuleProvider, TerraformStack, TerraformVariable

from imports.oci.provider import OciProvider
from imports.oci.identity_compartment import IdentityCompartment

from imports.oke import Oke

from lab.constructs import Budget


class Lab(TerraformStack):
    def __init__(
        self,
        scope: Construct,
        id: str,
    ):
        super().__init__(scope, id)

        tenancy_ocid = TerraformVariable(self, "oci_tenancy_ocid", type="string")
        user_ocid = TerraformVariable(self, "oci_user_ocid", type="string")
        fingerprint = TerraformVariable(self, "oci_fingerprint", type="string")
        region = TerraformVariable(self, "oci_region", type="string")
        private_key = TerraformVariable(
            self, "oci_private_key", type="string", sensitive=True
        )

        alerts_email = TerraformVariable(self, "alerts_email", type="string")

        oci = OciProvider(
            self,
            "oci",
            tenancy_ocid=tenancy_ocid.string_value,
            user_ocid=user_ocid.string_value,
            fingerprint=fingerprint.string_value,
            region=region.string_value,
            private_key=private_key.string_value,
        )

        Budget(
            self,
            "budget",
            name="primary",
            compartment_id=tenancy_ocid.string_value,
            amount=15,
            forecasted_alert_thresholds=[100.0, 200.0],
            actual_alert_thresholds=[50.0, 100.0, 200.0],
            alert_recipients=[alerts_email.string_value],
        )

        lab = IdentityCompartment(
            self,
            "lab",
            compartment_id=tenancy_ocid.string_value,
            description="Lab",
            name="lab",
        )

        Oke(
            self,
            "lab_cluster",

            cluster_name="lab",
            kubernetes_version="v1.29.1",
            tenancy_id=tenancy_ocid.string_value,
            compartment_id=lab.compartment_id,

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

            providers=[
                TerraformModuleProvider(module_alias="home", provider=oci)
            ],
        )
