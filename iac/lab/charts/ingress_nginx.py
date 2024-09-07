from cdk8s import Chart
from constructs import Construct

from lab.libs.config import IngressConfig
from lab.libs.exceptions import LabError
from lab.libs.k8s.include import Include
from lab.libs.k8s.api_object import patch_obj


class IngressNginx(Chart):
    VERSION = "1.10.1"

    INGRESS_CLASS_NAME = "nginx"

    MANIFEST_URL = f"https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v{VERSION}/deploy/static/provider/cloud/deploy.yaml"

    def __init__(self, scope: Construct, id_: str, config: IngressConfig):
        super().__init__(scope, id_)

        ing = Include(
            self,
            "ingress-nginx",
            url=IngressNginx.MANIFEST_URL,
        )

        ##
        ## Patch Service
        ##
        if not (
            svc := ing.find_object(kind="Service", name="ingress-nginx-controller")
        ):
            raise LabError(
                "could not find service/ingress-nginx-controller in ingress-nginx manifest"
            )

        patch_obj(
            svc,
            "/metadata/annotations",
            {
                "oci.oraclecloud.com/load-balancer-type": "nlb",
                "oci-network-load-balancer.oraclecloud.com/oci-network-security-groups": config.oci_public_load_balancer_nsg_ocid,
            },
        )

        ##
        ## Patch ConfigMap
        ##
        if not (
            cfg := ing.find_object(kind="Configmap", name="ingress-nginx-controller")
        ):
            raise LabError(
                "could not find configmap/ingress-nginx-controller in ingress-nginx manifest"
            )

        patch_obj(cfg, "/data/allow-snippet-annotations", "true")
