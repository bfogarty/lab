from ipaddress import IPv4Network
from typing import IO, Optional
from pydantic import BaseModel, ValidationError, SecretStr

from lab.libs.exceptions import ConfigError

import yaml


class CloudflareAcmeIssuerConfig(BaseModel):
    email: str
    api_token: SecretStr
    dns_zones: list[str]


class CloudflareDnsConfig(BaseModel):
    domain: str
    api_token: SecretStr
    local_network_cidr: IPv4Network


class TailscaleClusterApiProxy(BaseModel):
    cluster_admins: list[str] = []


class TailscaleConfig(BaseModel):
    client_id: str
    client_secret: SecretStr
    cluster_api_proxy: Optional[TailscaleClusterApiProxy] = None


class IngressConfig(BaseModel):
    oci_public_load_balancer_nsg_ocid: str


class Config(BaseModel):
    tailscale: TailscaleConfig
    cloudflare_acme_issuer: CloudflareAcmeIssuerConfig
    cloudflare_dns: CloudflareDnsConfig
    ingress: IngressConfig


def parse_config(raw_config: IO) -> Config:
    try:
        return Config.model_validate(yaml.safe_load(raw_config))
    except yaml.YAMLError as e:
        raise ConfigError(f"error parsing yaml: {e}") from e
    except ValidationError as e:
        raise ConfigError(f"error in config: {e}") from e
