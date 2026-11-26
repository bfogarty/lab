from typing import cast
from constructs import Construct

from cdk8s import ApiObject, Chart

from lab.libs.config import TailscaleClusterApiProxy, TailscaleConfig
from lab.libs.exceptions import LabError
from lab.libs.k8s.include import Include
from lab.libs.k8s.api_object import (
    patch_obj,
    set_deployment_container_env,
    set_deployment_container_image,
)

import cdk8s_plus_29 as kplus


def _update_oauth_secret(ts: Include, client_id: str, client_secret: str) -> None:
    if not (oauth_secret := ts.find_object(kind="Secret", name="operator-oauth")):
        raise LabError("could not find secret/operator-oauth in tailscale manifest")

    patch_obj(oauth_secret, "/stringData/client_id", client_id)
    patch_obj(oauth_secret, "/stringData/client_secret", client_secret)


def _configure_api_proxy(
    ts: Include,
    operator_deployment: ApiObject,
    api_proxy_config: TailscaleClusterApiProxy,
) -> None:
    # safe: Include may not be the root of the scope tree
    scope = cast(Construct, ts.node.scope)

    set_deployment_container_env(
        operator_deployment,
        container_name="operator",
        env_name="APISERVER_PROXY",
        env_value="true",
    )

    kplus.ClusterRoleBinding(
        scope,
        "cluster-admins",
        role=kplus.ClusterRole.from_cluster_role_name(
            scope, "cluster-admin", name="cluster-admin"
        ),
    ).add_subjects(
        *[
            kplus.User.from_name(scope, f"user-{i}", name=x)
            for i, x in enumerate(api_proxy_config.cluster_admins)
        ]
    )


class Tailscale(Chart):
    # pinned release, used by the manifest URL and image tags below. when
    # upgrading, pick a version with a "Tailscale Kubernetes Operator" entry in
    # https://tailscale.com/changelog. only those releases ship images.
    OPERATOR_VERSION = "1.104.7"

    OPERATOR_IMAGE = f"docker.io/tailscale/k8s-operator:v{OPERATOR_VERSION}"

    PROXY_IMAGE = f"docker.io/tailscale/tailscale:v{OPERATOR_VERSION}"

    MANIFEST_BASE_URL = f"https://raw.githubusercontent.com/tailscale/tailscale/v{OPERATOR_VERSION}/cmd/k8s-operator/deploy/manifests"

    def __init__(self, scope: Construct, id_: str, *, config: TailscaleConfig):
        super().__init__(scope, id_)

        ts = self._include_operator_manifest()

        _update_oauth_secret(
            ts,
            config.client_id,
            config.client_secret.get_secret_value(),
        )

        if not (
            operator_deployment := ts.find_object(kind="Deployment", name="operator")
        ):
            raise LabError("could not find deployment/operator in tailscale manifest")

        # upstream's manifests use the `stable`/`unstable` tags, which change
        # with each release (tailscale/tailscale#10655) and can drift from the
        # manifest version if not pinned.
        set_deployment_container_image(
            operator_deployment,
            container_name="operator",
            image=Tailscale.OPERATOR_IMAGE,
        )
        set_deployment_container_env(
            operator_deployment,
            container_name="operator",
            env_name="PROXY_IMAGE",
            env_value=Tailscale.PROXY_IMAGE,
        )

        if config.operator_hostname:
            set_deployment_container_env(
                operator_deployment,
                container_name="operator",
                env_name="OPERATOR_HOSTNAME",
                env_value=config.operator_hostname,
            )

        if config.cluster_api_proxy:
            self._include_authproxy_rbac_manifest()
            _configure_api_proxy(ts, operator_deployment, config.cluster_api_proxy)

    def _include_operator_manifest(self) -> Include:
        return Include(
            self,
            "tailscale",
            url=f"{Tailscale.MANIFEST_BASE_URL}/operator.yaml",
        )

    def _include_authproxy_rbac_manifest(self) -> Include:
        return Include(
            self,
            "tailscale-authproxy-rbac",
            url=f"{Tailscale.MANIFEST_BASE_URL}/authproxy-rbac.yaml",
        )
