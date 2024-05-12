from constructs import Construct
from cdktf import TerraformStack, TerraformVariable

from imports.oci.provider import OciProvider


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

        OciProvider(
            self,
            "oci",
            tenancy_ocid=tenancy_ocid.string_value,
            user_ocid=user_ocid.string_value,
            fingerprint=fingerprint.string_value,
            region=region.string_value,
            private_key=private_key.string_value,
        )
