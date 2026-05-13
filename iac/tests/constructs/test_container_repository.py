import json
from collections.abc import Generator
from typing import Any

import cdktf
import pytest

from lab.constructs.container_repository import PrivateContainerRepository

COMPARTMENT_ID = "ocid1.tenancy.oc1..test"
REPO_NAME = "test-repo"


class TestPrivateContainerRepositoryDefaults:
    @pytest.fixture(scope="class")
    def resource(self) -> Generator[dict[str, Any], None, None]:
        app = cdktf.Testing.app()
        stack = cdktf.TerraformStack(app, "test")
        PrivateContainerRepository(stack, "repo", name=REPO_NAME, compartment_id=COMPARTMENT_ID)
        synthesized = json.loads(cdktf.Testing.synth(stack))
        yield next(iter(synthesized["resource"]["oci_artifacts_container_repository"].values()))

    def test_display_name(self, resource: dict[str, Any]) -> None:
        assert resource["display_name"] == REPO_NAME

    def test_compartment_id(self, resource: dict[str, Any]) -> None:
        assert resource["compartment_id"] == COMPARTMENT_ID

    def test_is_public_false(self, resource: dict[str, Any]) -> None:
        assert resource["is_public"] is False

    def test_is_immutable_defaults_false(self, resource: dict[str, Any]) -> None:
        assert resource["is_immutable"] is False


class TestPrivateContainerRepositoryImmutable:
    @pytest.fixture(scope="class")
    def resource(self) -> Generator[dict[str, Any], None, None]:
        app = cdktf.Testing.app()
        stack = cdktf.TerraformStack(app, "test")
        PrivateContainerRepository(stack, "repo", name=REPO_NAME, compartment_id=COMPARTMENT_ID, is_immutable=True)
        synthesized = json.loads(cdktf.Testing.synth(stack))
        yield next(iter(synthesized["resource"]["oci_artifacts_container_repository"].values()))

    def test_is_immutable(self, resource: dict[str, Any]) -> None:
        assert resource["is_immutable"] is True

    def test_is_still_private(self, resource: dict[str, Any]) -> None:
        assert resource["is_public"] is False
