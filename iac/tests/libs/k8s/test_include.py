import pytest
import cdk8s

from pathlib import Path
from lab.libs.k8s.include import Include


class TestInclude:
    @pytest.fixture
    def deployments(self) -> Include:
        return Include(
            cdk8s.Testing.chart(),
            "include",
            url=str(Path(__file__).parent / "deployments.yaml"),
        )

    def test_find_object(self, deployments: Include) -> None:
        obj = deployments.find_object(kind="Deployment", name="nginx-deployment")

        assert isinstance(obj, cdk8s.ApiObject)
        assert obj.kind == "Deployment"
        assert obj.name == "nginx-deployment"

    def test_find_object_case_insensitive(self, deployments: Include) -> None:
        assert (
            deployments.find_object(kind="Deployment", name="nginx-deployment")
            is not None
        )
        assert (
            deployments.find_object(kind="deployment", name="nginx-deployment")
            is not None
        )

    def test_find_object_not_found(self, deployments: Include) -> None:
        assert deployments.find_object(kind="Deployment", name="deployment") is None
