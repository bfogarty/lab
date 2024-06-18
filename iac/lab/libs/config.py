from typing import IO
from pydantic import BaseModel, ValidationError, SecretStr

from lab.libs.exceptions import ConfigError

import yaml


class Config(BaseModel):
    tailscale_client_id: str
    tailscale_client_secret: SecretStr


def parse_config(raw_config: IO) -> Config:
    try:
        return Config.model_validate(yaml.safe_load(raw_config))
    except yaml.YAMLError as e:
        raise ConfigError(f"error parsing yaml: {e}") from e
    except ValidationError as e:
        raise ConfigError(f"error in config: {e}") from e
