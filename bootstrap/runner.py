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
    DEV_ENV_NAME,
    DEV_ENV_SLUG,
    DUMPS_DIR,
    ENV_TO_CLUSTER_DEFAULT,
    FRONTEND_TEMPLATE_URLS,
    GITLAB_URL_DEFAULT,
    MEDIA_STORAGE_DIGITALOCEAN_S3,
    MINOS_PLATFORM_IMAGE,
    MINOS_SERVICE_IMAGE,
    NODE_VERSION_DEFAULT,
    OPENTOFU_COMPONENT_VERSION,
    OPENTOFU_VERSION,
    PROD_ENV_NAME,
    PROD_ENV_SLUG,
    PYTHON_VERSION_DEFAULT,
    SERVICE_SLUG_DEFAULT,
    STAGE_ENV_NAME,
    STAGE_ENV_SLUG,
    SUBREPOS_DIR,
    TERRAFORM_BACKEND_TFC,
)
from bootstrap.exceptions import BootstrapError
from bootstrap.helpers import format_gitlab_variable

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
    terraform_backend: str
    terraform_cloud_hostname: str | None = None
    terraform_cloud_token: str | None = None
    terraform_cloud_organization: str | None = None
    terraform_cloud_organization_create: bool | None = None
    terraform_cloud_admin_email: str | None = None
    vault_token: str | None = None
    vault_url: str | None = None
    digitalocean_token: str | None = None
    clusters: list[str] | None = None
    cluster_core_providers: dict[str, list[str]] | None = None
    env_to_cluster: dict[str, str] | None = None
    python_version: str = PYTHON_VERSION_DEFAULT
    node_version: str = NODE_VERSION_DEFAULT
    minos_platform_image: str = MINOS_PLATFORM_IMAGE
    minos_service_image: str = MINOS_SERVICE_IMAGE
    opentofu_component_version: str = OPENTOFU_COMPONENT_VERSION
    opentofu_version: str = OPENTOFU_VERSION
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
    gitlab_token: str | None = None
    gitlab_namespace_path: str | None = None
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
    envs: list = field(init=False, default_factory=list)
    gitlab_variables: dict = field(init=False, default_factory=dict)
    vault_secrets: dict = field(init=False, default_factory=dict)
    terraform_run_modules: list = field(init=False, default_factory=list)
    terraform_outputs: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Finalize initialization."""
        self.service_slug = SERVICE_SLUG_DEFAULT
        self.gitlab_url = self.gitlab_url and self.gitlab_url.rstrip("/")
        self.run_id = f"{time():.0f}"
        self.terraform_dir = self.terraform_dir or Path(f".terraform/{self.run_id}")
        self.logs_dir = self.logs_dir or Path(f".logs/{self.run_id}")

    def set_envs(self):
        """Set the envs."""
        env_to_cluster = self.env_to_cluster or ENV_TO_CLUSTER_DEFAULT

        def _host(url: str) -> str:
            return (url or "").removeprefix("https://").removeprefix("http://").rstrip("/")

        self.envs = [
            {
                "basic_auth_enabled": True,
                "name": DEV_ENV_NAME,
                "prefix": self.subdomain_dev,
                "slug": DEV_ENV_SLUG,
                "cluster_slug": env_to_cluster.get(DEV_ENV_NAME),
                "host": _host(self.project_url_dev),
                "url": self.project_url_dev,
            },
            {
                "basic_auth_enabled": True,
                "name": STAGE_ENV_NAME,
                "prefix": self.subdomain_stage,
                "slug": STAGE_ENV_SLUG,
                "cluster_slug": env_to_cluster.get(STAGE_ENV_NAME),
                "host": _host(self.project_url_stage),
                "url": self.project_url_stage,
            },
            {
                "basic_auth_enabled": False,
                "name": PROD_ENV_NAME,
                "prefix": self.subdomain_prod,
                "slug": PROD_ENV_SLUG,
                "cluster_slug": env_to_cluster.get(PROD_ENV_NAME),
                "host": _host(self.project_url_prod),
                "url": self.project_url_prod,
            },
        ]

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
        if self.vault_url:
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
            ("SENTRY_AUTH_TOKEN", self.sentry_auth_token, True)
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

    def register_vault_platform_secret(self, cluster_slug, secret_name, secret_data):
        """Register a Vault platform secret at platforms/{cluster}/{name}."""
        self.vault_secrets[f"platforms/{cluster_slug}/{secret_name}"] = secret_data

    def register_vault_environment_secret(self, env_name, secret_name, secret_data):
        """Register a Vault environment secret locally."""
        self.vault_secrets[f"envs/{env_name}/{secret_name}"] = secret_data

    def collect_vault_platform_secrets(self, cluster_slug):
        """Collect the Vault secrets for the given cluster (platform layer)."""
        if not self.digitalocean_token:
            return
        digitalocean_credentials = {"token": self.digitalocean_token}
        if self.media_storage == MEDIA_STORAGE_DIGITALOCEAN_S3:
            digitalocean_credentials["spaces_access_id"] = self.s3_access_id
            digitalocean_credentials["spaces_secret_key"] = self.s3_secret_key
        self.register_vault_platform_secret(
            cluster_slug,
            "digitalocean",
            {"digitalocean_credentials": digitalocean_credentials},
        )

    def collect_vault_environment_secrets(self, env_name):
        """Collect the Vault secrets for the given environment."""
        self.register_vault_environment_secret(
            env_name,
            f"{self.service_slug}/basic_auth",
            {
                "basic_auth_username": self.project_slug,
                "basic_auth_password": secrets.token_urlsafe(12),
            },
        )
        # Sentry secrets are used by the GitLab CI/CD
        self.sentry_org and self.register_vault_environment_secret(
            env_name, "sentry", {"sentry_auth_token": self.sentry_auth_token}
        )

    def collect_vault_pact_secrets(self):
        """Collect the Vault secrets for Pact."""
        # Pact secrets are used by the GitLab CI/CD
        pact_broker_url = self.pact_broker_url
        pact_broker_username = self.pact_broker_username
        pact_broker_password = self.pact_broker_password
        pact_broker_auth_url = re.sub(
            r"^(https?)://(.*)$",
            rf"\g<1>://{pact_broker_username}:{pact_broker_password}@\g<2>",
            pact_broker_url,
        )
        self.vault_secrets["pact"] = {
            "pact_broker_base_url": pact_broker_url,
            "pact_broker_username": pact_broker_username,
            "pact_broker_password": pact_broker_password,
            "pact_broker_auth_url": pact_broker_auth_url,
        }

    def collect_vault_secrets(self):
        """Collect Vault secrets."""
        regcred = None
        if gitlab_terraform_outputs := self.terraform_outputs.get("gitlab"):
            regcred = {
                "registry_username": gitlab_terraform_outputs["registry_username"],
                "registry_password": gitlab_terraform_outputs["registry_password"],
            }
        for cluster_slug in self.clusters or []:
            self.collect_vault_platform_secrets(cluster_slug)
        for env in self.envs:
            env_name = env["name"]
            self.collect_vault_environment_secrets(env_name)
            regcred and self.register_vault_environment_secret(
                env_name, f"{self.service_slug}/regcred", regcred
            )
        self.pact_broker_url and self.collect_vault_pact_secrets()

    def init_service(self):
        """Initialize the service."""
        click.echo(info("...cookiecutting the service"))
        cookiecutter(
            os.path.dirname(os.path.dirname(__file__)),
            extra_context={
                "backend_service_port": self.backend_service_port,
                "backend_service_slug": self.backend_service_slug,
                "backend_type": self.backend_type,
                "frontend_service_port": self.frontend_service_port,
                "frontend_service_slug": self.frontend_service_slug,
                "frontend_type": self.frontend_type,
                "media_storage": self.media_storage,
                "minos_platform_image": self.minos_platform_image,
                "minos_service_image": self.minos_service_image,
                "opentofu_component_version": self.opentofu_component_version,
                "opentofu_version": self.opentofu_version,
                "project_dirname": self.project_dirname,
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "python_version": self.python_version,
                "resources": {"envs": self.envs},
                "service_slug": self.service_slug,
                "terraform_backend": self.terraform_backend,
                "terraform_cloud_organization": self.terraform_cloud_organization,
                "use_pact": self.pact_broker_url and "true" or "false",
                "use_vault": self.vault_url and "true" or "false",
            },
            output_dir=self.output_dir,
            no_input=True,
        )
        self.render_minos_per_cluster_files()

    def render_minos_per_cluster_files(self):
        """Write per-cluster minos tfvars skeletons (core/{provider}.tfvars + kubernetes.tfvars)."""
        click.echo(info("...generating per-cluster minos files"))
        clusters = self.clusters or []
        cluster_core_providers = self.cluster_core_providers or {}
        letsencrypt_email = self.letsencrypt_certificate_email or "tech@20tab.com"
        platform_dir = self.output_dir / self.project_dirname / "minos"
        for cluster in clusters:
            cluster_full = f"{self.project_slug}-{cluster}"
            cluster_dir = platform_dir / cluster
            (cluster_dir / "core").mkdir(parents=True, exist_ok=True)
            namespaces = sorted(
                {f"{self.project_slug}-{env['slug']}" for env in self.envs if env.get("cluster_slug") == cluster}
            )
            traefik_host = (
                f"proxy-{cluster}.{self.project_domain}" if self.project_domain else ""
            )
            for provider in cluster_core_providers.get(cluster, []):
                if provider == "digitalocean":
                    (cluster_dir / "core" / "digitalocean.tfvars").write_text(
                        f'cluster_slug                  = "{cluster_full}"\n'
                        'create_database               = true\n'
                        'create_valkey                 = false\n'
                        'database_cluster_node_size    = "db-s-1vcpu-2gb"\n'
                        'database_cluster_storage_size = 10\n'
                        'k8s_cluster_node_count        = 1\n'
                        'k8s_cluster_node_size         = "s-2vcpu-4gb"\n'
                        f'project_name                  = "{self.project_name}"\n'
                    )
                elif provider == "aws":
                    (cluster_dir / "core" / "aws.tfvars").write_text(
                        f'cluster_slug                  = "{cluster_full}"\n'
                        'iam_permissions_boundary_name = ""\n'
                        'iam_user_name_prefix          = ""\n'
                        'iam_users                     = {}\n'
                        'kms_keys                      = {}\n'
                    )
            (cluster_dir / "kubernetes.tfvars").write_text(
                f'cluster_slug                        = "{cluster_full}"\n'
                'managed_secrets                     = {}\n'
                f'namespaces                          = {json.dumps(namespaces)}\n'
                f'traefik_dashboard_host              = "{traefik_host}"\n'
                f'traefik_dashboard_letsencrypt_email = "{letsencrypt_email}"\n'
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
        env = {
            "TF_VAR_gitlab_url": self.gitlab_url,
            "TF_VAR_gitlab_token": self.gitlab_token,
            "TF_VAR_group_maintainers": self.gitlab_group_maintainers,
            "TF_VAR_group_name": self.project_name,
            "TF_VAR_group_namespace_path": self.gitlab_namespace_path,
            "TF_VAR_group_owners": self.gitlab_group_owners,
            "TF_VAR_group_slug": self.gitlab_group_slug,
            "TF_VAR_group_variables": self.render_gitlab_variables_to_string("group"),
            "TF_VAR_local_repository_dir": self.service_dir,
            "TF_VAR_project_description": (
                f'The "{self.project_name}" project {self.service_slug} service.'
            ),
            "TF_VAR_project_name": self.service_slug.title(),
            "TF_VAR_project_slug": self.service_slug,
            "TF_VAR_project_variables": self.render_gitlab_variables_to_string(
                "project"
            ),
            "TF_VAR_use_vault": self.vault_url and "true" or "false",
        }
        self.gitlab_url != GITLAB_URL_DEFAULT and env.update(
            GITLAB_BASE_URL=f"{self.gitlab_url}/api/v4/"
        )
        self.run_terraform(
            "gitlab", env, outputs=["registry_password", "registry_username"]
        )

    def init_terraform_cloud(self):
        """Initialize the Terraform Cloud resources."""
        click.echo(info("...creating the Terraform Cloud resources with Terraform"))
        env = {
            "TF_VAR_admin_email": self.terraform_cloud_admin_email,
            "TF_VAR_cluster_core_providers": json.dumps(self.cluster_core_providers or {}),
            "TF_VAR_clusters": json.dumps(self.clusters or []),
            "TF_VAR_create_organization": self.terraform_cloud_organization_create
            and "true"
            or "false",
            "TF_VAR_hostname": self.terraform_cloud_hostname,
            "TF_VAR_organization_name": self.terraform_cloud_organization,
            "TF_VAR_project_name": self.project_name,
            "TF_VAR_project_slug": self.project_slug,
            "TF_VAR_terraform_cloud_token": self.terraform_cloud_token,
        }
        self.run_terraform("terraform-cloud", env)

    def init_vault(self):
        """Initialize the Vault resources."""
        click.echo(info("...creating the Vault resources with Terraform"))
        # NOTE: Vault secrets collection must be done AFTER GitLab init
        self.collect_vault_secrets()
        env = {
            "TF_VAR_project_name": self.project_name,
            "TF_VAR_project_slug": self.project_slug,
            "TF_VAR_secrets": json.dumps(self.vault_secrets),
            "TF_VAR_vault_address": self.vault_url,
            "TF_VAR_vault_token": self.vault_token,
        }
        self.terraform_backend == TERRAFORM_BACKEND_TFC and env.update(
            TF_VAR_terraform_cloud_token=self.terraform_cloud_token
        )
        self.run_terraform("vault", env)

    def get_terraform_module_params(self, module_name, env):
        """Return Terraform parameters for the given module."""
        return (
            Path(__file__).parent.parent / "terraform" / module_name,
            self.logs_dir / self.service_slug / "terraform" / module_name,
            terraform_dir := self.terraform_dir / self.service_slug / module_name,
            {
                **env,
                "PATH": os.environ.get("PATH"),
                "TF_DATA_DIR": str((terraform_dir / "data").resolve()),
                "TF_LOG": "INFO",
            },
        )

    def run_terraform_init(self, cwd, env, logs_dir, state_path):
        """Run Terraform init."""
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
        if init_process.returncode != 0:
            init_stderr_path.write_text(init_process.stderr)
            click.echo(
                error(
                    "Terraform init failed "
                    f"(check {init_stderr_path} and {init_log_path})"
                )
            )
            raise BootstrapError

    def run_terraform_apply(self, cwd, env, logs_dir):
        """Run Terraform apply."""
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
        if apply_process.returncode != 0:
            apply_stderr_path.write_text(apply_process.stderr)
            click.echo(
                error(
                    "Terraform apply failed "
                    f"(check {apply_stderr_path} and {apply_log_path})"
                )
            )
            self.reset_terraform()
            raise BootstrapError

    def run_terraform_destroy(self, cwd, env, logs_dir):
        """Run Terraform destroy."""
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
                    "Terraform destroy failed "
                    f"(check {destroy_stderr_path} and {destroy_log_path})"
                )
            )
            raise BootstrapError

    def get_terraform_outputs(self, cwd, env, outputs):
        """Get Terraform outputs."""
        return {
            output_name: subprocess.run(
                ["terraform", "output", "-raw", output_name],
                capture_output=True,
                cwd=cwd,
                env=env,
                text=True,
            ).stdout
            for output_name in outputs
        }

    def reset_terraform(self):
        """Destroy all Terraform modules resources."""
        for module_name, env in self.terraform_run_modules:
            click.echo(warning(f"Destroying Terraform {module_name} resources."))
            cwd, logs_dir, _terraform_dir, env = self.get_terraform_module_params(
                module_name, env
            )
            self.run_terraform_destroy(cwd, env, logs_dir)

    def run_terraform(self, module_name, env, outputs=None):
        """Initialize the Terraform controlled resources."""
        self.terraform_run_modules.append((module_name, env))
        cwd, logs_dir, terraform_dir, env = self.get_terraform_module_params(
            module_name, env
        )
        os.makedirs(terraform_dir, exist_ok=True)
        os.makedirs(logs_dir)
        self.run_terraform_init(cwd, env, logs_dir, terraform_dir / "terraform.tfstate")
        self.run_terraform_apply(cwd, env, logs_dir)
        outputs and self.terraform_outputs.update(
            {module_name: self.get_terraform_outputs(cwd, env, outputs)}
        )

    def make_sed(self, file_path, placeholder, replace_value):
        """Replace a placeholder value with a given one in a given file."""
        target_file = self.output_dir / self.project_dirname / file_path
        target_file.write_text(
            target_file.read_text().replace(placeholder, replace_value)
        )

    def init_subrepo(self, service_slug, template_url, **kwargs):
        """Initialize a subrepo using the given template and options."""
        subrepo_dir = str((SUBREPOS_DIR / service_slug).resolve())
        shutil.rmtree(subrepo_dir, ignore_errors=True)
        subprocess.run(
            [
                "git",
                "clone",
                template_url,
                subrepo_dir,
                "-q",
            ]
        )
        options = {
            "env_to_cluster": self.env_to_cluster,
            "gid": self.gid,
            "gitlab_namespace_path": str(
                Path(self.gitlab_namespace_path) / self.gitlab_group_slug
            ),
            "gitlab_token": self.gitlab_token,
            "gitlab_url": self.gitlab_url,
            "logs_dir": str(self.logs_dir.resolve()),
            "minos_service_image": self.minos_service_image,
            "opentofu_component_version": self.opentofu_component_version,
            "opentofu_version": self.opentofu_version,
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
            capture_output=True,
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
        shutil.rmtree(DUMPS_DIR, ignore_errors=True)
        shutil.rmtree(SUBREPOS_DIR, ignore_errors=True)
        shutil.rmtree(self.terraform_dir, ignore_errors=True)

    def run(self):
        """Run the bootstrap."""
        click.echo(highlight(f"Initializing the {self.service_slug} service:"))
        self.set_envs()
        self.collect_gitlab_variables()
        self.init_service()
        self.create_env_file()
        if self.terraform_backend == TERRAFORM_BACKEND_TFC:
            self.init_terraform_cloud()
        if self.gitlab_group_slug:
            self.init_gitlab()
        if self.vault_url:
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
                node_version=self.node_version,
                sentry_dsn=self.frontend_sentry_dsn,
            )
        backend_template_url = BACKEND_TEMPLATE_URLS.get(self.backend_type)
        if backend_template_url:
            self.init_subrepo(
                self.backend_service_slug,
                backend_template_url,
                internal_service_port=self.backend_service_port,
                media_storage=self.media_storage,
                python_version=self.python_version,
                sentry_dsn=self.backend_sentry_dsn,
            )
        self.change_output_owner()
        self.cleanup()
