"""Run the bootstrap."""

import base64
import json
import os
import re
import secrets
import shutil
import subprocess
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from time import time

import click
from cookiecutter.main import cookiecutter
from pydantic import validate_arguments

from bootstrap.constants import (
    BACKEND_TEMPLATE_URLS,
    DEPLOYMENT_TYPE_OTHER,
    DEV_ENV_NAME,
    DEV_ENV_SLUG,
    DEV_STACK_SLUG,
    DUMPS_DIR,
    FRONTEND_TEMPLATE_URLS,
    GITLAB_URL_DEFAULT,
    MAIN_STACK_SLUG,
    MEDIA_STORAGE_DIGITALOCEAN_S3,
    PROD_ENV_NAME,
    PROD_ENV_SLUG,
    SERVICE_SLUG_DEFAULT,
    STAGE_ENV_NAME,
    STAGE_ENV_SLUG,
    STAGE_STACK_SLUG,
    SUBREPOS_DIR,
    TERRAFORM_BACKEND_TFC,
)
from bootstrap.exceptions import BootstrapError
from bootstrap.helpers import format_gitlab_variable, format_tfvar

error = partial(click.style, fg="red")

highlight = partial(click.style, fg="cyan")

info = partial(click.style, dim=True)

warning = partial(click.style, fg="yellow")


@validate_arguments
@dataclass(kw_only=True)
class Runner:
    """The bootstrap runner."""

    output_dir: Path
    project_name: str
    project_slug: str
    project_dirname: str
    service_dir: Path
    backend_type: str
    backend_service_slug: str | None = None
    backend_service_port: int | None = None
    frontend_type: str
    frontend_service_slug: str | None = None
    frontend_service_port: int | None = None
    deployment_type: str
    terraform_backend: str
    terraform_cloud_hostname: str | None = None
    terraform_cloud_token: str | None = None
    terraform_cloud_organization: str | None = None
    terraform_cloud_organization_create: bool | None = None
    terraform_cloud_admin_email: str | None = None
    vault_token: str | None = None
    vault_url: str | None = None
    digitalocean_token: str | None = None
    kubernetes_cluster_ca_certificate: str | None = None
    kubernetes_host: str | None = None
    kubernetes_token: str | None = None
    environment_distribution: str
    project_domain: str | None = None
    subdomain_dev: str | None = None
    subdomain_stage: str | None = None
    subdomain_prod: str | None = None
    subdomain_monitoring: str | None = None
    project_url_dev: str = ""
    project_url_stage: str = ""
    project_url_prod: str = ""
    letsencrypt_certificate_email: str | None = None
    digitalocean_domain_create: bool | None = None
    digitalocean_dns_records_create: bool | None = None
    digitalocean_k8s_cluster_region: str | None = None
    digitalocean_database_cluster_region: str | None = None
    digitalocean_database_cluster_node_size: str | None = None
    postgres_image: str | None = None
    postgres_persistent_volume_capacity: str | None = None
    postgres_persistent_volume_claim_capacity: str | None = None
    postgres_persistent_volume_host_path: str | None = None
    use_redis: bool = False
    redis_image: str | None = None
    digitalocean_redis_cluster_region: str | None = None
    digitalocean_redis_cluster_node_size: str | None = None
    sentry_org: str | None = None
    sentry_url: str | None = None
    sentry_auth_token: str | None = None
    backend_sentry_dsn: str | None = None
    frontend_sentry_dsn: str | None = None
    pact_broker_url: str | None = None
    pact_broker_username: str | None = None
    pact_broker_password: str | None = None
    media_storage: str
    s3_region: str | None = None
    s3_host: str | None = None
    s3_access_id: str | None = None
    s3_secret_key: str | None = None
    s3_bucket_name: str | None = None
    gitlab_url: str | None = None
    gitlab_private_token: str | None = None
    gitlab_group_slug: str | None = None
    gitlab_group_owners: str | None = None
    gitlab_group_maintainers: str | None = None
    gitlab_group_developers: str | None = None
    uid: int | None = None
    gid: int | None = None
    terraform_dir: Path | None = None
    logs_dir: Path | None = None
    run_id: str = field(init=False)
    service_slug: str = field(init=False)
    stacks_environments: dict = field(init=False, default_factory=dict)
    gitlab_variables: dict = field(init=False, default_factory=dict)
    tfvars: dict = field(init=False, default_factory=dict)
    vault_project_path: str = field(init=False, default="")
    vault_secrets: dict = field(init=False, default_factory=dict)
    terraform_outputs: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Finalize initialization."""
        self.service_slug = SERVICE_SLUG_DEFAULT
        self.gitlab_url = self.gitlab_url.rstrip("/")
        self.run_id = f"{time():.0f}"
        self.terraform_dir = self.terraform_dir or Path(f".terraform/{self.run_id}")
        self.logs_dir = self.logs_dir or Path(f".logs/{self.run_id}")
        self.set_vault_project_path()
        self.set_stacks_environments()
        self.collect_tfvars()
        self.collect_gitlab_variables()

    def set_vault_project_path(self):
        """Set the Vault project path."""
        if self.vault_url:
            self.vault_project_path = self.gitlab_group_slug or self.project_slug

    def set_stacks_environments(self):
        """Set the environments distribution per stack."""
        dev_env = {
            "name": DEV_ENV_NAME,
            "prefix": self.subdomain_dev,
            "url": self.project_url_dev,
        }
        stage_env = {
            "name": STAGE_ENV_NAME,
            "prefix": self.subdomain_stage,
            "url": self.project_url_stage,
        }
        prod_env = {
            "name": PROD_ENV_NAME,
            "prefix": self.subdomain_prod,
            "url": self.project_url_prod,
        }
        if self.environment_distribution == "1":
            self.stacks_environments = {
                MAIN_STACK_SLUG: {
                    DEV_ENV_SLUG: dev_env,
                    STAGE_ENV_SLUG: stage_env,
                    PROD_ENV_SLUG: prod_env,
                }
            }
        elif self.environment_distribution == "2":
            self.stacks_environments = {
                DEV_STACK_SLUG: {DEV_ENV_SLUG: dev_env, STAGE_ENV_SLUG: stage_env},
                MAIN_STACK_SLUG: {PROD_ENV_SLUG: prod_env},
            }
        elif self.environment_distribution == "3":
            self.stacks_environments = {
                DEV_STACK_SLUG: {DEV_ENV_SLUG: dev_env},
                STAGE_STACK_SLUG: {STAGE_ENV_SLUG: stage_env},
                MAIN_STACK_SLUG: {PROD_ENV_SLUG: prod_env},
            }

    def register_gitlab_variable(
        self, level, var_name, var_value=None, masked=False, protected=True
    ):
        """Register a GitLab variable at the given level."""
        vars_dict = self.gitlab_variables.setdefault(level, {})
        if var_value is None:
            var_value = getattr(self, var_name)
        vars_dict[var_name] = format_gitlab_variable(var_value, masked, protected)

    def register_gitlab_variables(self, level, *vars):
        """Register one or more GitLab variable at the given level."""
        [
            self.register_gitlab_variable(level, *((i,) if isinstance(i, str) else i))
            for i in vars
        ]

    def register_gitlab_group_variables(self, *vars):
        """Register one or more GitLab group variable."""
        self.register_gitlab_variables("group", *vars)

    def register_gitlab_project_variables(self, *vars):
        """Register one or more GitLab project variable."""
        self.register_gitlab_variables("project", *vars)

    def collect_gitlab_variables(self):
        """Collect the GitLab group and project variables."""
        if self.pact_broker_url:
            self.register_gitlab_group_variables(("PACT_ENABLED", "true", False, False))
        if self.vault_token:
            self.register_gitlab_group_variables(
                ("VAULT_ADDR", self.vault_url, False, False)
            )
        else:
            self.collect_gitlab_variables_secrets()

    def collect_gitlab_variables_secrets(self):
        """Collect secrets as GitLab group and project variables."""
        self.register_gitlab_group_variables(
            ("BASIC_AUTH_USERNAME", self.project_slug),
            ("BASIC_AUTH_PASSWORD", secrets.token_urlsafe(12), True),
        )
        self.sentry_org and self.register_gitlab_group_variables(
            "SENTRY_AUTH_TOKEN", self.sentry_auth_token, True
        )
        if self.pact_broker_url:
            pact_broker_url = self.pact_broker_url
            pact_broker_username = self.pact_broker_username
            pact_broker_password = self.pact_broker_password
            pact_broker_auth_url = re.sub(
                r"^(https?)://(.*)$",
                rf"\g<1>://{pact_broker_username}:{pact_broker_password}@\g<2>",
                pact_broker_url,
            )
            self.register_gitlab_group_variables(
                ("PACT_BROKER_BASE_URL", pact_broker_url, False, False),
                ("PACT_BROKER_USERNAME", pact_broker_username, False, False),
                ("PACT_BROKER_PASSWORD", pact_broker_password, True, False),
                ("PACT_BROKER_AUTH_URL", pact_broker_auth_url, True, False),
            )
        if self.terraform_backend == TERRAFORM_BACKEND_TFC:
            self.register_gitlab_group_variables(
                ("TFC_TOKEN", self.terraform_cloud_token, True)
            )
        if self.subdomain_monitoring:
            self.register_gitlab_project_variables(
                ("GRAFANA_PASSWORD", secrets.token_urlsafe(12), True)
            )
        self.digitalocean_token and self.register_gitlab_group_variables(
            ("DIGITALOCEAN_TOKEN", self.digitalocean_token, True)
        )
        if self.deployment_type == DEPLOYMENT_TYPE_OTHER:
            self.register_gitlab_group_variables(
                (
                    "KUBERNETES_CLUSTER_CA_CERTIFICATE",
                    base64.b64encode(
                        Path(self.kubernetes_cluster_ca_certificate).read_bytes()
                    ).decode(),
                    True,
                ),
                ("KUBERNETES_HOST", self.kubernetes_host),
                ("KUBERNETES_TOKEN", self.kubernetes_token, True),
            )
        if "s3" in self.media_storage:
            self.register_gitlab_group_variables(
                ("S3_ACCESS_ID", self.s3_access_id, True),
                ("S3_REGION", self.s3_region),
                ("S3_SECRET_KEY", self.s3_secret_key, True),
            )
            self.s3_bucket_name and self.register_gitlab_group_variables(
                ("S3_BUCKET_NAME", self.s3_bucket_name)
            )
            (
                self.media_storage == MEDIA_STORAGE_DIGITALOCEAN_S3
                and self.register_gitlab_group_variables(("S3_HOST", self.s3_host))
            )

    def render_gitlab_variables_to_string(self, level):
        """Return the given level GitLab variables rendered to string."""
        return "{%s}" % ", ".join(
            f"{k} = {v}" for k, v in self.gitlab_variables.get(level, {}).items()
        )

    def register_tfvar(self, tf_stage, var_name, var_value=None, var_type=None):
        """Register a Terraform variable value for the given stage."""
        vars_list = self.tfvars.setdefault(tf_stage, [])
        if var_value is None:
            var_value = getattr(self, var_name)
        vars_list.append("=".join((var_name, format_tfvar(var_value, var_type))))

    def register_tfvars(self, tf_stage, *vars):
        """Register one or more Terraform variable for the given stage."""
        [
            self.register_tfvar(tf_stage, *((i,) if isinstance(i, str) else i))
            for i in vars
        ]

    def register_base_tfvars(self, *vars, stack_slug=None):
        """Register one or more base Terraform variable."""
        tf_stage = "base" + (stack_slug and f"_{stack_slug}" or "")
        self.register_tfvars(tf_stage, *vars)

    def register_cluster_tfvars(self, *vars, stack_slug=None):
        """Register one or more cluster Terraform variable."""
        tf_stage = "cluster" + (stack_slug and f"_{stack_slug}" or "")
        self.register_tfvars(tf_stage, *vars)

    def register_environment_tfvars(self, *vars, env_slug=None):
        """Register one or more environment Terraform variable."""
        tf_stage = "environment" + (env_slug and f"_{env_slug}" or "")
        self.register_tfvars(tf_stage, *vars)

    def collect_tfvars(self):
        """Collect the base, cluster and environment Terraform variables."""
        backend_service_paths = ["/"]
        frontend_service_paths = ["/"]
        if self.frontend_service_slug:
            self.register_environment_tfvars(
                ("frontend_service_paths", frontend_service_paths, "list"),
                ("frontend_service_port", None, "num"),
                "frontend_service_slug",
            )
            backend_service_paths = ["/admin", "/api", "/static"] + (
                ["/media"] if self.media_storage == "local" else []
            )
        if self.backend_service_slug:
            self.register_environment_tfvars(
                ("backend_service_paths", backend_service_paths, "list"),
                ("backend_service_port", None, "num"),
                "backend_service_slug",
            )
        self.project_domain and self.register_environment_tfvars("project_domain")
        if self.letsencrypt_certificate_email:
            self.register_cluster_tfvars("letsencrypt_certificate_email")
            self.register_environment_tfvars("letsencrypt_certificate_email")
        self.subdomain_monitoring and self.register_environment_tfvars(
            ("monitoring_subdomain", self.subdomain_monitoring), env_slug="prod"
        )
        if self.use_redis:
            self.register_base_tfvars(("use_redis", True, "bool"))
            self.register_environment_tfvars(("use_redis", True, "bool"))
        if "digitalocean" in self.deployment_type:
            self.register_environment_tfvars(
                ("create_dns_records", self.digitalocean_dns_records_create, "bool"),
            )
            self.digitalocean_domain_create and self.register_environment_tfvars(
                ("create_domain", True, "bool"), env_slug=DEV_ENV_SLUG
            )
            self.register_base_tfvars(
                ("k8s_cluster_region", self.digitalocean_k8s_cluster_region),
                ("database_cluster_region", self.digitalocean_database_cluster_region),
                (
                    "database_cluster_node_size",
                    self.digitalocean_database_cluster_node_size,
                ),
            )
            self.use_redis and self.register_base_tfvars(
                ("redis_cluster_region", self.digitalocean_redis_cluster_region),
                ("redis_cluster_node_size", self.digitalocean_redis_cluster_node_size),
            )
        elif self.deployment_type == DEPLOYMENT_TYPE_OTHER:
            self.register_environment_tfvars(
                "postgres_image",
                "postgres_persistent_volume_capacity",
                "postgres_persistent_volume_claim_capacity",
                "postgres_persistent_volume_host_path",
            )
            self.use_redis and self.register_environment_tfvars("redis_image")
        if self.media_storage == MEDIA_STORAGE_DIGITALOCEAN_S3:
            self.register_base_tfvars(("create_s3_bucket", True, "bool"))
            self.register_environment_tfvars(
                ("digitalocean_spaces_bucket_available", True, "bool")
            )
        for stack_slug, stack_envs in self.stacks_environments.items():
            for env_slug, _env_data in stack_envs.items():
                self.register_environment_tfvars(
                    ("basic_auth_enabled", env_slug != "prod", "bool"),
                    ("stack_slug", stack_slug),
                    ("subdomains", [getattr(self, f"subdomain_{env_slug}")], "list"),
                    env_slug=env_slug,
                )

    def register_vault_stack_secret(self, stack_slug, name, data):
        """Register a Vault stack secret locally."""
        self.vault_secrets[f"stacks/{stack_slug}/{name}"] = data

    def register_vault_environment_secret(self, env_slug, name, data):
        """Register a Vault environment secret locally."""
        self.vault_secrets[f"envs/{env_slug}/{name}"] = data

    def collect_vault_stack_secrets(self, stack_slug):
        """Collect the Vault secrets for the given stack."""
        self.digitalocean_token and self.register_vault_stack_secret(
            stack_slug, "digitalocean", dict(digitalocean_token=self.digitalocean_token)
        )
        if "s3" in self.media_storage:
            s3_secret = dict(
                s3_region=self.s3_region,
                s3_access_id=self.s3_access_id,
                s3_secret_key=self.s3_secret_key,
            )
            self.s3_bucket_name and s3_secret.update(s3_bucket_name=self.s3_bucket_name)
            self.media_storage == MEDIA_STORAGE_DIGITALOCEAN_S3 and s3_secret.update(
                s3_host=self.s3_host
            )
            self.register_vault_stack_secret(stack_slug, "s3", s3_secret)
        (
            self.subdomain_monitoring
            and stack_slug == MAIN_STACK_SLUG
            and self.register_vault_stack_secret(
                stack_slug,
                "monitoring",
                dict(grafana_password=secrets.token_urlsafe(12)),
            )
        )
        (
            self.deployment_type == DEPLOYMENT_TYPE_OTHER
            and self.register_vault_stack_secret(
                stack_slug,
                "k8s",
                dict(
                    kubernetes_cluster_ca_certificate=base64.b64encode(
                        Path(self.kubernetes_cluster_ca_certificate).read_bytes()
                    ).decode(),
                    kubernetes_host=self.kubernetes_host,
                    kubernetes_token=self.kubernetes_token,
                ),
            )
        )

    def collect_vault_environment_secrets(self, env_slug):
        """Collect the Vault secrets for the given environment."""
        self.register_vault_environment_secret(
            env_slug,
            "basic_auth",
            dict(
                basic_auth_username=self.project_slug,
                basic_auth_password=secrets.token_urlsafe(12),
            ),
        )
        # Sentry and Pact env vars are used by the GitLab CI/CD
        self.sentry_org and self.register_vault_environment_secret(
            env_slug, "sentry", dict(sentry_auth_token=self.sentry_auth_token)
        )
        if self.pact_broker_url:
            pact_broker_url = self.pact_broker_url
            pact_broker_username = self.pact_broker_username
            pact_broker_password = self.pact_broker_password
            pact_broker_auth_url = re.sub(
                r"^(https?)://(.*)$",
                rf"\g<1>://{pact_broker_username}:{pact_broker_password}@\g<2>",
                pact_broker_url,
            )
            self.register_vault_environment_secret(
                env_slug,
                "pact",
                dict(
                    pact_broker_base_url=pact_broker_url,
                    pact_broker_username=pact_broker_username,
                    pact_broker_password=pact_broker_password,
                    pact_broker_auth_url=pact_broker_auth_url,
                ),
            )

    def collect_vault_secrets(self):
        """Collect Vault secrets."""
        regcred = None
        if gitlab_terraform_outputs := self.terraform_outputs.get("gitlab"):
            regcred = dict(
                registry_username=gitlab_terraform_outputs["registry_username"],
                registry_password=gitlab_terraform_outputs["registry_password"],
            )
        for stack_slug, stack_envs in self.stacks_environments.items():
            self.collect_vault_stack_secrets(stack_slug)
            for env_slug in stack_envs:
                self.collect_vault_environment_secrets(env_slug)
                regcred and self.register_vault_environment_secret(
                    env_slug, "regcred", regcred
                )

    def init_service(self):
        """Initialize the service."""
        click.echo(info("...cookiecutting the service"))
        cookiecutter(
            os.path.dirname(os.path.dirname(__file__)),
            extra_context={
                "backend_service_port": self.backend_service_port,
                "backend_service_slug": self.backend_service_slug,
                "backend_type": self.backend_type,
                "deployment_type": self.deployment_type,
                "environment_distribution": self.environment_distribution,
                "frontend_service_port": self.frontend_service_port,
                "frontend_service_slug": self.frontend_service_slug,
                "frontend_type": self.frontend_type,
                "media_storage": self.media_storage,
                "pact_enabled": bool(self.pact_broker_url),
                "project_dirname": self.project_dirname,
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "service_slug": self.service_slug,
                "stacks": self.stacks_environments,
                "terraform_backend": self.terraform_backend,
                "terraform_cloud_organization": self.terraform_cloud_organization,
                "tfvars": self.tfvars,
                "vault_project_path": self.vault_project_path,
            },
            output_dir=self.output_dir,
            no_input=True,
        )

    def create_env_file(self):
        """Create the final env file from its template."""
        click.echo(info("...generating the .env file"))
        env_path = self.service_dir / ".env_template"
        env_text = (
            env_path.read_text()
            .replace("__SECRETKEY__", secrets.token_urlsafe(40))
            .replace("__PASSWORD__", secrets.token_urlsafe(8))
        )
        (self.service_dir / ".env").write_text(env_text)

    def init_gitlab(self):
        """Initialize the GitLab resources."""
        click.echo(info("...creating the GitLab resources with Terraform"))
        env = dict(
            TF_VAR_gitlab_token=self.gitlab_private_token,
            TF_VAR_group_maintainers=self.gitlab_group_maintainers,
            TF_VAR_group_name=self.project_name,
            TF_VAR_group_owners=self.gitlab_group_owners,
            TF_VAR_group_slug=self.gitlab_group_slug,
            TF_VAR_group_variables=self.render_gitlab_variables_to_string("group"),
            TF_VAR_local_repository_dir=self.service_dir,
            TF_VAR_project_description=(
                f'The "{self.project_name}" project {self.service_slug} service.'
            ),
            TF_VAR_project_name=self.service_slug.title(),
            TF_VAR_project_slug=self.service_slug,
            TF_VAR_project_variables=self.render_gitlab_variables_to_string("project"),
            TF_VAR_vault_enabled=self.vault_url and "true" or "false",
        )
        self.gitlab_url != GITLAB_URL_DEFAULT and env.update(
            GITLAB_BASE_URL=f"{self.gitlab_url}/api/v4/"
        )
        self.run_terraform(
            "gitlab", env, outputs=["registry_password", "registry_username"]
        )

    def init_terraform_cloud(self):
        """Initialize the Terraform Cloud resources."""
        click.echo(info("...creating the Terraform Cloud resources with Terraform"))
        env = dict(
            TF_VAR_admin_email=self.terraform_cloud_admin_email,
            TF_VAR_create_organization=self.terraform_cloud_organization_create
            and "true"
            or "false",
            TF_VAR_environments=json.dumps(
                [i for j in self.stacks_environments.values() for i in j]
            ),
            TF_VAR_hostname=self.terraform_cloud_hostname,
            TF_VAR_organization_name=self.terraform_cloud_organization,
            TF_VAR_project_name=self.project_name,
            TF_VAR_project_slug=self.project_slug,
            TF_VAR_service_slug=self.service_slug,
            TF_VAR_stacks=json.dumps(list(self.stacks_environments)),
            TF_VAR_terraform_cloud_token=self.terraform_cloud_token,
        )
        self.run_terraform("terraform-cloud", env)

    def init_vault(self):
        """Initialize the Vault resources."""
        click.echo(info("...creating the Vault resources with Terraform"))
        # NOTE: Vault secrets collection must be done AFTER GitLab init
        self.collect_vault_secrets()
        env = dict(
            TF_VAR_project_name=self.project_name,
            TF_VAR_project_path=self.vault_project_path,
            TF_VAR_secrets=json.dumps(self.vault_secrets),
            VAULT_ADDR=self.vault_url,
            VAULT_TOKEN=self.vault_token,
        )
        self.terraform_backend == TERRAFORM_BACKEND_TFC and env.update(
            TF_VAR_terraform_cloud_token=self.terraform_cloud_token
        )
        self.run_terraform("vault", env)

    def run_terraform(self, module_name, env, outputs=None):
        """Initialize the Terraform controlled resources."""
        cwd = Path(__file__).parent.parent / "terraform" / module_name
        terraform_dir = self.terraform_dir / self.service_slug / module_name
        os.makedirs(terraform_dir, exist_ok=True)
        env.update(
            PATH=os.environ.get("PATH"),
            TF_DATA_DIR=str((terraform_dir / "data").resolve()),
            TF_LOG="INFO",
        )
        state_path = terraform_dir / "state.tfstate"
        logs_dir = self.logs_dir / self.service_slug / "terraform" / module_name
        os.makedirs(logs_dir)
        init_log_path = logs_dir / "init.log"
        init_stdout_path = logs_dir / "init-stdout.log"
        init_stderr_path = logs_dir / "init-stderr.log"
        init_process = subprocess.run(
            [
                "terraform",
                "init",
                "-backend-config",
                f"path={state_path.resolve()}",
                "-input=false",
                "-no-color",
            ],
            capture_output=True,
            cwd=cwd,
            env=dict(**env, TF_LOG_PATH=str(init_log_path.resolve())),
            text=True,
        )
        init_stdout_path.write_text(init_process.stdout)
        if init_process.returncode == 0:
            apply_log_path = logs_dir / "apply.log"
            apply_stdout_path = logs_dir / "apply-stdout.log"
            apply_stderr_path = logs_dir / "apply-stderr.log"
            apply_process = subprocess.run(
                ["terraform", "apply", "-auto-approve", "-input=false", "-no-color"],
                capture_output=True,
                cwd=cwd,
                env=dict(**env, TF_LOG_PATH=str(apply_log_path.resolve())),
                text=True,
            )
            apply_stdout_path.write_text(apply_process.stdout)
            for output_name in outputs or []:
                output_process = subprocess.run(
                    ["terraform", "output", "-raw", output_name],
                    capture_output=True,
                    cwd=cwd,
                    env=env,
                    text=True,
                )
                self.terraform_outputs.setdefault(module_name, {})[
                    output_name
                ] = output_process.stdout
            if apply_process.returncode != 0:
                apply_stderr_path.write_text(apply_process.stderr)
                click.echo(
                    error(
                        f"Error applying {module_name} Terraform configuration "
                        f"(check {apply_stderr_path} and {apply_log_path})"
                    )
                )
                destroy_log_path = logs_dir / "destroy.log"
                destroy_stdout_path = logs_dir / "destroy-stdout.log"
                destroy_stderr_path = logs_dir / "destroy-stderr.log"
                destroy_process = subprocess.run(
                    [
                        "terraform",
                        "destroy",
                        "-auto-approve",
                        "-input=false",
                        "-no-color",
                    ],
                    capture_output=True,
                    cwd=cwd,
                    env=dict(**env, TF_LOG_PATH=str(destroy_log_path.resolve())),
                    text=True,
                )
                destroy_stdout_path.write_text(destroy_process.stdout)
                if destroy_process.returncode != 0:
                    destroy_stderr_path.write_text(destroy_process.stderr)
                    click.echo(
                        error(
                            f"Error performing {module_name} Terraform destroy "
                            f"(check {destroy_stderr_path} and {destroy_log_path})"
                        )
                    )
                raise BootstrapError
        else:
            init_stderr_path.write_text(init_process.stderr)
            click.echo(
                error(
                    f"Error performing {module_name} Terraform init "
                    f"(check {init_stderr_path} and {init_log_path})"
                )
            )
            raise BootstrapError

    def init_subrepo(self, service_slug, template_url, **kwargs):
        """Initialize a subrepo using the given template and options."""
        subrepo_dir = str((SUBREPOS_DIR / service_slug).resolve())
        shutil.rmtree(subrepo_dir, ignore_errors=True)
        subprocess.run(
            [
                "git",
                "clone",
                "--branch",
                "feature/vault",
                template_url,
                subrepo_dir,
                "-q",
            ]
        )
        options = {
            "deployment_type": self.deployment_type,
            "environment_distribution": self.environment_distribution,
            "gid": self.gid,
            "gitlab_group_slug": self.gitlab_group_slug,
            "gitlab_private_token": self.gitlab_private_token,
            "logs_dir": str(self.logs_dir.resolve()),
            "output_dir": str(self.service_dir.resolve()),
            "project_dirname": service_slug,
            "project_name": self.project_name,
            "project_slug": self.project_slug,
            "project_url_dev": self.project_url_dev,
            "project_url_prod": self.project_url_prod,
            "project_url_stage": self.project_url_stage,
            "sentry_org": self.sentry_org,
            "sentry_url": self.sentry_url,
            "service_dir": str((self.service_dir / service_slug).resolve()),
            "service_slug": service_slug,
            "terraform_backend": self.terraform_backend,
            "terraform_cloud_admin_email": self.terraform_cloud_admin_email,
            "terraform_cloud_hostname": self.terraform_cloud_hostname,
            "terraform_cloud_organization_create": False,
            "terraform_cloud_organization": self.terraform_cloud_organization,
            "terraform_cloud_token": self.terraform_cloud_token,
            "terraform_dir": str(self.terraform_dir.resolve()),
            "uid": self.uid,
            "use_redis": self.use_redis,
            "vault_url": self.vault_url,
            "vault_token": self.vault_token,
            **kwargs,
        }
        subprocess.run(
            ["python", "-m", "pip", "install", "-r", "requirements/common.txt"],
            cwd=subrepo_dir,
        )
        subprocess.run(
            [
                "python",
                "-c",
                f"from bootstrap.runner import Runner; Runner(**{options}).run()",
            ],
            cwd=subrepo_dir,
        )

    def change_output_owner(self):
        """Change the owner of the output directory recursively."""
        if self.uid:
            subprocess.run(
                [
                    "chown",
                    "-R",
                    ":".join(map(str, filter(None, (self.uid, self.gid)))),
                    self.service_dir,
                ]
            )

    def cleanup(self):
        """Clean up after a successful execution."""
        shutil.rmtree(DUMPS_DIR)
        shutil.rmtree(SUBREPOS_DIR)
        shutil.rmtree(self.terraform_dir)

    def run(self):
        """Run the bootstrap."""
        click.echo(highlight(f"Initializing the {self.service_slug} service:"))
        self.init_service()
        self.create_env_file()
        if self.gitlab_group_slug:
            self.init_gitlab()
        if self.terraform_backend == TERRAFORM_BACKEND_TFC:
            self.init_terraform_cloud()
        if self.vault_token:
            self.init_vault()
        frontend_template_url = FRONTEND_TEMPLATE_URLS.get(self.frontend_type)
        if frontend_template_url:
            self.init_subrepo(
                self.frontend_service_slug,
                frontend_template_url,
                internal_backend_url=self.backend_service_slug
                and (f"http://{self.backend_service_slug}:{self.backend_service_port}")
                or None,
                internal_service_port=self.frontend_service_port,
                sentry_dsn=self.frontend_sentry_dsn,
            )
        backend_template_url = BACKEND_TEMPLATE_URLS.get(self.backend_type)
        if backend_template_url:
            self.init_subrepo(
                self.backend_service_slug,
                backend_template_url,
                internal_service_port=self.backend_service_port,
                media_storage=self.media_storage,
                sentry_dsn=self.backend_sentry_dsn,
            )
        self.change_output_owner()
        self.cleanup()
