from ipaddress import IPv4Network
from typing import IO, Optional
from pydantic import BaseModel, ValidationError, SecretStr

from lab.libs.exceptions import ConfigError

import yaml


class GrafanaServiceConfig(BaseModel):
    host: str
    username: str


class GrafanaConfig(BaseModel):
    cluster_name: str
    access_policy_token: SecretStr
    loki: GrafanaServiceConfig
    prometheus: GrafanaServiceConfig
    remote_config: GrafanaServiceConfig


class CloudflareAcmeIssuerConfig(BaseModel):
    email: str
    api_token: SecretStr
    dns_zones: list[str]


class CloudflareDnsConfig(BaseModel):
    domain: str
    api_token: SecretStr
    local_network_cidr: IPv4Network


class BitwardenSmtpConfig(BaseModel):
    host: str
    port: int
    username: str
    password: SecretStr
    use_explicit_tls: bool = True
    from_email: str
    from_name: str


class BitwardenConfig(BaseModel):
    admin_token: SecretStr
    smtp: BitwardenSmtpConfig
    domain: str
    organization_name: str
    icon_blacklist_regex: str = ""


class TailscaleClusterApiProxy(BaseModel):
    cluster_admins: list[str] = []


class TailscaleConfig(BaseModel):
    client_id: str
    client_secret: SecretStr
    cluster_api_proxy: Optional[TailscaleClusterApiProxy] = None


class IngressConfig(BaseModel):
    oci_public_load_balancer_nsg_ocid: str


class Config(BaseModel):
    bitwarden: BitwardenConfig
    tailscale: TailscaleConfig
    cloudflare_acme_issuer: CloudflareAcmeIssuerConfig
    cloudflare_dns: CloudflareDnsConfig
    grafana: GrafanaConfig
    ingress: IngressConfig


def parse_config(raw_config: IO) -> Config:
    try:
        return Config.model_validate(yaml.safe_load(raw_config))
    except yaml.YAMLError as e:
        raise ConfigError(f"error parsing yaml: {e}") from e
    except ValidationError as e:
        raise ConfigError(f"error in config: {e}") from e
