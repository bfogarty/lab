from cdk8s import Chart, Cron

from constructs import Construct

from lab.libs.config import InboxZeroConfig
from lab.libs.constants import K8S_MAX_NAME_LENGTH

import cdk8s_plus_29 as kplus


class InboxZero(Chart):
    VERSION = "1.7.28"
    NAMESPACE = "inbox-zero"

    CRONS = [
        ("/api/google/watch/all", Cron.daily()),
        ("/api/resend/summary/all", Cron.weekly()),
        ("/api/reply-tracker/disable-unused-auto-draft", Cron.daily()),
    ]

    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        config: InboxZeroConfig,
        ingress_class_name: str,
        cluster_issuer_name: str,
    ):
        super().__init__(scope, id_, namespace=InboxZero.NAMESPACE)

        ##
        ## Secret + ConfigMap
        ##
        secret = kplus.Secret(
            self,
            f"{id_}-secret",
            string_data={
                "DATABASE_URL": config.database.url.get_secret_value(),
                "DIRECT_URL": config.database.direct_url.get_secret_value(),
                "NEXTAUTH_SECRET": config.auth.nextauth_secret.get_secret_value(),
                "GOOGLE_CLIENT_SECRET": config.google.client_secret.get_secret_value(),
                "GOOGLE_ENCRYPT_SECRET": config.google.encrypt_secret.get_secret_value(),
                "GOOGLE_ENCRYPT_SALT": config.google.encrypt_salt.get_secret_value(),
                "GOOGLE_PUBSUB_VERIFICATION_TOKEN": config.google.pubsub_verification_token.get_secret_value(),
                "OPENAI_API_KEY": config.llm.openai_api_key.get_secret_value(),
                "INTERNAL_API_KEY": config.internal_api_key.get_secret_value(),
                "API_KEY_SALT": config.api_key_salt.get_secret_value(),
                "UPSTASH_REDIS_TOKEN": config.redis.upstash_token.get_secret_value(),
                "REDIS_URL": config.redis.url.get_secret_value(),
                "QSTASH_TOKEN": config.qstash.token.get_secret_value(),
                "QSTASH_CURRENT_SIGNING_KEY": config.qstash.current_signing_key.get_secret_value(),
                "QSTASH_NEXT_SIGNING_KEY": config.qstash.next_signing_key.get_secret_value(),
            },
        )

        configmap = kplus.ConfigMap(
            self,
            f"{id_}-configmap",
            data={
                "ADMINS": config.admins,
                "NEXTAUTH_URL": config.auth.nextauth_url,
                "GOOGLE_CLIENT_ID": config.google.client_id,
                "GOOGLE_PUBSUB_TOPIC_NAME": config.google.pubsub_topic_name,
                "DEFAULT_LLM_PROVIDER": config.llm.default_provider,
                "DEFAULT_LLM_MODEL": config.llm.default_model,
                "UPSTASH_REDIS_URL": config.redis.upstash_url,
            },
        )

        ##
        ## Deployment
        ##
        deployment = kplus.Deployment(
            self,
            id_,
            replicas=1,
        )

        deployment.add_container(
            image=f"ghcr.io/elie222/inbox-zero:{InboxZero.VERSION}",
            resources=kplus.ContainerResources(
                cpu=None,
                memory=None,
            ),
            env_from=[kplus.EnvFrom(config_map=configmap), kplus.EnvFrom(sec=secret)],
            ports=[
                kplus.ContainerPort(name="http", number=3000),
            ],
            liveness=kplus.Probe.from_http_get(path="/"),
            readiness=kplus.Probe.from_http_get(path="/"),
        )

        svc = deployment.expose_via_service()

        ##
        ## Jobs
        ##
        for endpoint, schedule in InboxZero.CRONS:
            cronjob = kplus.CronJob(
                self,
                f"{id_}-{self._format_cronjob_name(endpoint)}"[:K8S_MAX_NAME_LENGTH],
                schedule=schedule,
                namespace=InboxZero.NAMESPACE,
                restart_policy=kplus.RestartPolicy.ON_FAILURE,
                backoff_limit=3,
            )

            cronjob.add_container(
                image=f"curlimages/curl:latest",
                args=["-X", "POST", f"{svc.name}:3000{endpoint}"],
                resources=kplus.ContainerResources(cpu=None, memory=None),
            )

    def _format_cronjob_name(self, endpoint: str) -> str:
        return endpoint.replace("/api/", "").replace("/all", "").replace("/", "-")