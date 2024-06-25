from typing import Any

from lab.libs.exceptions import LabError
from lab.libs.k8s.api_object import set_deployment_container_env

import cdk8s
import cdk8s_plus_29 as kplus

from pathlib import Path
from lab.libs.k8s.include import Include
from tests.utils import get_default_container_env
import pytest


class TestSetDeploymentContainerEnv:
    def test_not_a_deployment(self) -> None:
        pod = kplus.Pod(cdk8s.Testing.chart(), "pod")

        with pytest.raises(
            LabError, match=f"resource '{pod.name}' is a Pod, expected Deployment"
        ):
            set_deployment_container_env(
                cdk8s.ApiObject.of(pod),
                container_name="nginx",
                env_name="test-env",
                env_value="test-value",
            )

    def test_container_not_found(self) -> None:
        deploy = kplus.Deployment(
            cdk8s.Testing.chart(),
            "deployment",
            containers=[kplus.ContainerProps(image="nginx/nginx")],
        )

        with pytest.raises(
            LabError, match=f"container 'nginx' not found in deployment/{deploy.name}"
        ):
            set_deployment_container_env(
                cdk8s.ApiObject.of(deploy),
                container_name="nginx",
                env_name="test-env",
                env_value="test-value",
            )

    def test_deployments_spec(self) -> None:
        include = Include(
            cdk8s.Testing.chart(),
            "include",
            url=str(Path(__file__).parent / "deployments.yaml"),
        )

        deploy = include.find_object(kind="Deployment", name="invalid-deployment")
        assert deploy, "error loading deployment fixture"

        with pytest.raises(
            LabError,
            match=f"error parsing containers, is 'invalid-deployment' a valid deployment?",
        ):
            set_deployment_container_env(
                deploy,
                container_name="nginx",
                env_name="test-env",
                env_value="test-value",
            )

    def test_deployment_without_existing_env(self) -> None:
        deploy = kplus.Deployment(
            cdk8s.Testing.chart(),
            "deployment",
            containers=[
                kplus.ContainerProps(
                    name="nginx",
                    image="nginx/nginx",
                )
            ],
        )

        set_deployment_container_env(
            cdk8s.ApiObject.of(deploy),
            container_name="nginx",
            env_name="test-a",
            env_value="test-value",
        )

        deploy_json = cdk8s.ApiObject.of(deploy).to_json()
        assert [
            {"name": "test-a", "value": "test-value"},
        ] == get_default_container_env(deploy_json)

    def test_deployment_with_existing_env(self) -> None:
        deploy = kplus.Deployment(
            cdk8s.Testing.chart(),
            "deployment",
            containers=[
                kplus.ContainerProps(
                    name="nginx",
                    image="nginx/nginx",
                    env_variables={
                        "test-a": kplus.EnvValue.from_value("test-value-old"),
                        "test-b": kplus.EnvValue.from_value("test-value-old"),
                        "test-c": kplus.EnvValue.from_value("test-value-old"),
                    },
                )
            ],
        )

        # assert on the existing order of the env vars
        deploy_json = cdk8s.ApiObject.of(deploy).to_json()
        assert [
            "test-a",
            "test-b",
            "test-c",
        ] == [x["name"] for x in get_default_container_env(deploy_json)]

        # update an env var in place
        set_deployment_container_env(
            cdk8s.ApiObject.of(deploy),
            container_name="nginx",
            env_name="test-b",
            env_value="test-value",
        )

        # add a new env var
        set_deployment_container_env(
            cdk8s.ApiObject.of(deploy),
            container_name="nginx",
            env_name="test-d",
            env_value="test-value",
        )

        # assert
        #   - order is preserved,
        #   - the existing env var is updated, and
        #   - the new env var is appended
        deploy_json = cdk8s.ApiObject.of(deploy).to_json()
        assert [
            {"name": "test-a", "value": "test-value-old"},
            {"name": "test-b", "value": "test-value"},
            {"name": "test-c", "value": "test-value-old"},
            {"name": "test-d", "value": "test-value"},
        ] == get_default_container_env(deploy_json)
