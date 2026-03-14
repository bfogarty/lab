from typing import ClassVar

from cdk8s import App
from pydantic import BaseModel


class BaseCluster:
    config_class: ClassVar[type[BaseModel]]

    def __init__(self, app: App, config: BaseModel) -> None:
        pass
