from typing import Any
from cdk8s import ApiObject

from lab.libs.exceptions import LabError
from cdk8s import JsonPatch


def patch_obj(resource: ApiObject, path: str, data: Any) -> None:
    resource.add_json_patch(JsonPatch.add(path, data))


def set_deployment_container_env(
    deployment: ApiObject, *, container_name: str, env_name: str, env_value: str
) -> None:
    """
    Sets an environment variable on a container in a Deployment spec.
    """

    _deployment_name = deployment.metadata.name

    # validate that the given ApiObject is a deployment
    if deployment.kind != "Deployment":
        raise LabError(
            f"resource '{_deployment_name}' is a {deployment.kind}, expected Deployment"
        )

    # get the index of the the container with the given name
    try:
        containers = deployment.to_json()["spec"]["template"]["spec"]["containers"]
        container_index = next(
            i
            for i, container in enumerate(containers)
            if container["name"] == container_name
        )
    except StopIteration:
        raise LabError(
            f"container '{container_name}' not found in deployment/{_deployment_name}"
        )
    except KeyError:
        raise LabError(
            f"error parsing containers, is '{_deployment_name}' a valid deployment?"
        )

    # update the environment
    current_env = containers[container_index].get("env", [])

    if env_name in [x["name"] for x in current_env]:
        # if the env contains the variable, update in place, preserving order
        new_env = [
            e if e["name"] != env_name else {"name": env_name, "value": env_value}
            for e in current_env
        ]
    else:
        # if the env does not contain the variable, append it
        new_env = current_env + [{"name": env_name, "value": env_value}]

    patch_obj(
        deployment,
        f"/spec/template/spec/containers/{container_index}/env",
        new_env,
    )
