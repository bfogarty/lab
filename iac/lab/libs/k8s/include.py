from typing import Optional, cast

from cdk8s import ApiObject, Include as BaseInclude


class Include(BaseInclude):
    """
    Wraps `cdk8s.Include` to add utilities for modifying the included YAML.
    """

    def find_object(self, *, kind: str, name: str) -> Optional[ApiObject]:
        for x in self.node.children:
            x_obj = ApiObject.of(x)

            if x_obj.kind.lower() == kind.lower() and x_obj.name == name:
                return x_obj

        return None
