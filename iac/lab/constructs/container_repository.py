from constructs import Construct

from imports.oci.artifacts_container_repository import ArtifactsContainerRepository


class PrivateContainerRepository(Construct):
    """
    Creates a private container repository in an OCI Compartment.

    Args:
        scope: The parent construct scope.
        id_: The unique identifier for this construct.
        name: The display name of the container repository.
        compartment_id: The OCID of the compartment in which to create the repository.
        is_immutable: When true, prevents pushing new images to existing tags.
            Defaults to False.
    """

    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        name: str,
        compartment_id: str,
        is_immutable: bool = False,
    ):
        super().__init__(scope, id_)

        self.repository = ArtifactsContainerRepository(
            self,
            "repository",
            compartment_id=compartment_id,
            display_name=name,
            is_public=False,
            is_immutable=is_immutable,
        )
