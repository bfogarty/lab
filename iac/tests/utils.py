import pytest
from typing import Any

from re import Pattern


def str_match(a: str, b: str | Pattern) -> bool:
    if isinstance(b, Pattern):
        return bool(b.match(a))

    return a == b


def get_default_container_env(deploy_json: Any) -> list[dict]:
    assert deploy_json.get("kind") == "Deployment", "object is not a Deployment"

    try:
        return deploy_json["spec"]["template"]["spec"]["containers"][0].get("env", [])
    except (KeyError, IndexError):
        pytest.fail("Deployment spec is not valid")


def get_resource(obj: list[Any], kind: str, name: str | Pattern) -> Any:
    try:
        return next(
            x
            for x in obj
            if x["kind"] == kind and str_match(x["metadata"]["name"], name)
        )
    except KeyError:
        return None
