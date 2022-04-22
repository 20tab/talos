"""Run the bootstrap."""

import base64
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

from bootstrap.constants import (
    BACKEND_TEMPLATE_URLS,
    DEPLOYMENT_TYPE_OTHER,
    FRONTEND_TEMPLATE_URLS,
    MEDIA_STORAGE_AWS_S3,
    MEDIA_STORAGE_DIGITALOCEAN_S3,
    ORCHESTRATOR_SERVICE_SLUG,
    SUBREPOS_DIR,
    TERRAFORM_BACKEND_GITLAB,
    TERRAFORM_BACKEND_TFC,
)
from bootstrap.exceptions import BootstrapError
from bootstrap.helpers import format_tfvar

error = partial(click.style, fg="red")

highlight = partial(click.style, fg="cyan")

info = partial(click.style, dim=True)

warning = partial(click.style, fg="yellow")


@dataclass(kw_only=True)
class Runner:
    """The bootstrap runner."""

    uid: int
    gid: int
    output_dir: Path
    project_name: str
    project_slug: str
    project_dirname: str
    service_dir: Path
    backend_type: str
    backend_service_slug: str
    backend_service_port: int
    frontend_type: str
    frontend_service_slug: str
    frontend_service_port: int
    deployment_type: str
    terraform_backend: str
    terraform_cloud_hostname: str
    terraform_cloud_token: str
    terraform_cloud_organization: str
    terraform_cloud_organization_create: str
    terraform_cloud_admin_email: str
    digitalocean_token: str
    kubernetes_cluster_ca_certificate: str
    kubernetes_host: str
    kubernetes_token: str
    environment_distribution: str
    project_domain: str
    domain_prefix_dev: str
    domain_prefix_stage: str
    domain_prefix_prod: str
    domain_prefix_monitoring: str
    project_url_dev: str
    project_url_stage: str
    project_url_prod: str
    project_url_monitoring: str
    letsencrypt_certificate_email: str
    digitalocean_create_domain: str
    digitalocean_k8s_cluster_region: str
    digitalocean_database_cluster_region: str
    digitalocean_database_cluster_node_size: str
    postgres_image: str
    postgres_persistent_volume_capacity: str
    postgres_persistent_volume_claim_capacity: str
    postgres_persistent_volume_host_path: str
    use_redis: str
    redis_image: str
    digitalocean_redis_cluster_region: str
    digitalocean_redis_cluster_node_size: str
    sentry_org: str
    sentry_url: str
    backend_sentry_dsn: str
    frontend_sentry_dsn: str
    sentry_auth_token: str
    pact_broker_url: str
    pact_broker_username: str
    pact_broker_password: str
    media_storage: str
    s3_region: str
    s3_host: str
    s3_access_id: str
    s3_secret_key: str
    s3_bucket_name: str
    gitlab_private_token: str
    gitlab_group_slug: str
    gitlab_group_owners: str
    gitlab_group_maintainers: str
    gitlab_group_developers: str
    terraform_dir: Path
    logs_dir: Path
    run_id: str = field(init=False)
    service_slug: str = field(init=False)
    stacks_environments: dict = field(init=False, default_factory=dict)
    tfvars: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Finalize initialization."""
        self.service_slug = ORCHESTRATOR_SERVICE_SLUG
        self.run_id = f"{time():.0f}"
        self.terraform_dir = self.terraform_dir or Path(f".terraform/{self.run_id}")
        self.logs_dir = self.logs_dir or Path(f".logs/{self.run_id}")
        self.set_stacks_environments()
        self.set_tfvars()

    def set_stacks_environments(self):
        """Set the environments distribution per stack."""
        dev_env = {
            "name": "Development",
            "url": self.project_url_dev,
            "prefix": self.domain_prefix_dev,
        }
        stage_env = {
            "name": "Staging",
            "url": self.project_url_stage,
            "prefix": self.domain_prefix_stage,
        }
        prod_env = {
            "name": "Production",
            "url": self.project_url_prod,
            "prefix": self.domain_prefix_prod,
        }
        if self.environment_distribution == "1":
            self.stacks_environments = {
                "main": {"dev": dev_env, "stage": stage_env, "prod": prod_env}
            }
        elif self.environment_distribution == "2":
            self.stacks_environments = {
                "dev": {"dev": dev_env, "stage": stage_env},
                "main": {"prod": prod_env},
            }
        elif self.environment_distribution == "3":
            self.stacks_environments = {
                "dev": {"dev": dev_env},
                "stage": {"stage": stage_env},
                "main": {"prod": prod_env},
            }

    def add_tfvar(self, tf_stage, var_name, var_value=None, var_type=None):
        """Add a Terraform value to the given .tfvars file."""
        vars_list = self.tfvars.setdefault(tf_stage, [])
        if var_value is None:
            var_value = getattr(self, var_name)
        vars_list.append("=".join((var_name, format_tfvar(var_value, var_type))))

    def add_tfvars(self, tf_stage, *vars):
        """Add one or more Terraform variables to the given stage."""
        [self.add_tfvar(tf_stage, *((i,) if isinstance(i, str) else i)) for i in vars]

    def add_base_tfvars(self, *vars, stack_slug=None):
        """Add one or more base Terraform variables."""
        tf_stage = "base" + (stack_slug and f"_{stack_slug}" or "")
        self.add_tfvars(tf_stage, *vars)

    def add_cluster_tfvars(self, *vars, stack_slug=None):
        """Add one or more cluster Terraform variables."""
        tf_stage = "cluster" + (stack_slug and f"_{stack_slug}" or "")
        self.add_tfvars(tf_stage, *vars)

    def add_environment_tfvars(self, *vars, env_slug=None):
        """Add one or more environment Terraform variables."""
        tf_stage = "environment" + (env_slug and f"_{env_slug}" or "")
        self.add_tfvars(tf_stage, *vars)

    def set_tfvars(self):
        """Set base, cluster and environment Terraform variables lists."""
        backend_service_paths = ["/"]
        frontend_service_paths = ["/"]
        if self.frontend_service_slug:
            self.add_environment_tfvars(
                ("frontend_service_paths", frontend_service_paths, "list"),
                ("frontend_service_port", None, "num"),
                "frontend_service_slug",
            )
            backend_service_paths = ["/admin", "/api", "/static"] + (
                ["/media"] if self.media_storage == "local" else []
            )
        if self.backend_service_slug:
            self.add_environment_tfvars(
                ("backend_service_paths", backend_service_paths, "list"),
                ("backend_service_port", None, "num"),
                "backend_service_slug",
            )
        self.project_domain and self.add_cluster_tfvars("project_domain")
        self.letsencrypt_certificate_email and self.add_cluster_tfvars(
            "letsencrypt_certificate_email",
            ("ssl_enabled", True, "bool"),
        )
        if self.use_redis:
            self.add_base_tfvars(("use_redis", True, "bool"))
            self.add_environment_tfvars(("use_redis", True, "bool"))
        if self.project_url_monitoring:
            self.add_cluster_tfvars(
                ("monitoring_url", self.project_url_monitoring),
            )
            self.domain_prefix_monitoring and self.add_cluster_tfvars(
                ("monitoring_domain_prefix", self.domain_prefix_monitoring),
            )
        if "digitalocean" in self.deployment_type:
            self.project_domain and self.add_cluster_tfvars(
                ("create_domain", self.digitalocean_create_domain, "bool")
            )
            self.add_base_tfvars(
                ("k8s_cluster_region", self.digitalocean_k8s_cluster_region),
                ("database_cluster_region", self.digitalocean_database_cluster_region),
                (
                    "database_cluster_node_size",
                    self.digitalocean_database_cluster_node_size,
                ),
            )
            self.use_redis and self.add_base_tfvars(
                ("redis_cluster_region", self.digitalocean_redis_cluster_region),
                ("redis_cluster_node_size", self.digitalocean_redis_cluster_node_size),
            )
        elif self.deployment_type == DEPLOYMENT_TYPE_OTHER:
            self.add_environment_tfvars(
                "postgres_image",
                "postgres_persistent_volume_capacity",
                "postgres_persistent_volume_claim_capacity",
                "postgres_persistent_volume_host_path",
            )
            self.use_redis and self.add_environment_tfvars("redis_image")
        if self.media_storage == MEDIA_STORAGE_DIGITALOCEAN_S3:
            self.add_base_tfvars(("create_s3_bucket", True, "bool"))
            self.add_environment_tfvars(
                ("digitalocean_spaces_bucket_available", True, "bool")
            )
        for stack_slug, stack_envs in self.stacks_environments.items():
            domain_prefixes = []
            for env_slug, env_data in stack_envs.items():
                self.add_environment_tfvars(
                    ("basic_auth_enabled", env_slug != "prod", "bool"),
                    ("project_url", env_data["url"]),
                    ("stack_slug", stack_slug),
                    env_slug=env_slug,
                )
                if env_prefix := env_data["prefix"]:
                    domain_prefixes.append(env_prefix)
                    self.add_environment_tfvars(
                        ("domain_prefix", env_prefix), env_slug=env_slug
                    )
            domain_prefixes and self.add_cluster_tfvars(
                ("domain_prefixes", domain_prefixes, "list"), stack_slug=stack_slug
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
                "project_dirname": self.project_dirname,
                "project_domain": self.project_domain,
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "stacks": self.stacks_environments,
                "terraform_backend": self.terraform_backend,
                "tfvars": self.tfvars,
            },
            output_dir=self.output_dir,
            no_input=True,
        )

    def create_env_file(self):
        """Create the final env file from its template."""
        click.echo(info("...generating the .env file"))
        env_path = Path(self.service_dir) / ".env_template"
        env_text = (
            env_path.read_text()
            .replace("__SECRETKEY__", secrets.token_urlsafe(40))
            .replace("__PASSWORD__", secrets.token_urlsafe(8))
        )
        (Path(self.service_dir) / ".env").write_text(env_text)

    def init_subrepo(self, service_slug, template_url, **kwargs):
        """Initialize a subrepo using the given template and options."""
        subrepo_dir = str((Path(SUBREPOS_DIR) / service_slug).resolve())
        shutil.rmtree(subrepo_dir, ignore_errors=True)
        subprocess.run(
            [
                "git",
                "clone",
                template_url,
                subrepo_dir,
                "--branch",
                "feature/terraform-cloud",
                "-q",
            ]
        )
        options = {
            "deployment_type": self.deployment_type,
            "environment_distribution": self.environment_distribution,
            "gid": self.gid,
            "gitlab_group_slug": self.gitlab_group_slug,
            "gitlab_private_token": self.gitlab_private_token,
            "logs_dir": self.logs_dir,
            "output_dir": self.service_dir,
            "project_dirname": service_slug,
            "project_name": self.project_name,
            "project_slug": self.project_slug,
            "project_url_dev": self.project_url_dev,
            "project_url_prod": self.project_url_prod,
            "project_url_stage": self.project_url_stage,
            "service_dir": str((Path(self.service_dir) / service_slug).resolve()),
            "service_slug": service_slug,
            "terraform_backend": self.terraform_backend,
            "terraform_dir": self.terraform_dir,
            "uid": self.uid,
            "use_redis": self.use_redis,
            **kwargs,
        }
        subprocess.run(
            ["python", "-m", "pip", "install", "-r", "requirements/common.txt"],
            cwd=subrepo_dir,
        )
        subprocess.run(
            ["python", "-c", f"from setup import run; run(**{options})"],
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

    def get_gitlab_variables(self):
        """Return the GitLab group and project variables."""
        gitlab_group_variables = dict(
            BASIC_AUTH_USERNAME=('{value = "%s"}' % self.project_slug),
            BASIC_AUTH_PASSWORD=(
                '{value = "%s", masked = true}' % secrets.token_urlsafe(12)
            ),
        )
        gitlab_project_variables = {}
        # Sentry and Pact env vars are used by the GitLab CI/CD
        self.sentry_org and gitlab_group_variables.update(
            SENTRY_ORG='{value = "%s"}' % self.sentry_org,
            SENTRY_URL='{value = "%s"}' % self.sentry_url,
            SENTRY_AUTH_TOKEN='{value = "%s", masked = true}' % self.sentry_auth_token,
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
            gitlab_group_variables.update(
                PACT_ENABLED='{value = "true", protected = false}',
                PACT_BROKER_BASE_URL=(
                    '{value = "%s", protected = false}' % pact_broker_url
                ),
                PACT_BROKER_USERNAME=(
                    '{value = "%s", protected = false}' % pact_broker_username
                ),
                PACT_BROKER_PASSWORD=(
                    '{value = "%s", masked = true, protected = false}'
                    % pact_broker_password
                ),
                PACT_BROKER_AUTH_URL=(
                    '{value = "%s", masked = true, protected = false}'
                    % pact_broker_auth_url
                ),
            )
        # TODO: extend after implementing Vault
        if self.terraform_backend == TERRAFORM_BACKEND_TFC:
            gitlab_group_variables.update(
                TFC_TOKEN='{value = "%s", masked = true}' % self.terraform_cloud_token,
            )
        elif self.terraform_backend == TERRAFORM_BACKEND_GITLAB:
            if self.project_url_monitoring:
                gitlab_project_variables.update(
                    GRAFANA_PASSWORD='{value = "%s", masked = true}'
                    % secrets.token_urlsafe(12),
                )
            self.digitalocean_token and gitlab_group_variables.update(
                DIGITALOCEAN_TOKEN='{value = "%s", masked = true}'
                % self.digitalocean_token
            )
            if self.deployment_type == DEPLOYMENT_TYPE_OTHER:
                gitlab_group_variables.update(
                    KUBERNETES_CLUSTER_CA_CERTIFICATE='{value = "%s", masked = true}'
                    % base64.b64encode(
                        Path(self.kubernetes_cluster_ca_certificate).read_bytes()
                    ).decode(),
                    KUBERNETES_HOST='{value = "%s"}' % self.kubernetes_host,
                    KUBERNETES_TOKEN='{value = "%s", masked = true}'
                    % self.kubernetes_token,
                )
            "s3" in self.media_storage and gitlab_group_variables.update(
                S3_ACCESS_ID='{value = "%s", masked = true}' % self.s3_access_id,
                S3_SECRET_KEY='{value = "%s", masked = true}' % self.s3_secret_key,
                S3_REGION='{value = "%s"}' % self.s3_region,
                S3_HOST='{value = "%s"}' % self.s3_host,
            )
            if self.media_storage == MEDIA_STORAGE_DIGITALOCEAN_S3:
                gitlab_group_variables.update(
                    S3_HOST='{value = "%s"}' % self.s3_host,
                )
            elif self.media_storage == MEDIA_STORAGE_AWS_S3:
                gitlab_group_variables.update(
                    S3_BUCKET_NAME='{value = "%s"}' % self.s3_bucket_name,
                )
        return gitlab_group_variables, gitlab_project_variables

    def init_terraform_cloud(self):
        """Initialize Terraform Cloud workspace."""

    def init_gitlab(self):
        """Initialize the GitLab repositories."""
        click.echo(info("...creating the GitLab repository and associated resources"))
        group_variables, project_variables = self.get_gitlab_variables()
        terraform_dir = self.terraform_dir / self.service_slug
        os.makedirs(terraform_dir, exist_ok=True)
        env = dict(
            PATH=os.environ.get("PATH"),
            TF_DATA_DIR=str((terraform_dir / "data").resolve()),
            TF_LOG="INFO",
            TF_VAR_gitlab_group_developers=self.gitlab_group_developers,
            TF_VAR_gitlab_group_maintainers=self.gitlab_group_maintainers,
            TF_VAR_gitlab_group_owners=self.gitlab_group_owners,
            TF_VAR_gitlab_group_slug=self.gitlab_group_slug,
            TF_VAR_gitlab_group_variables="{%s}"
            % ", ".join(f"{k} = {v}" for k, v in group_variables.items()),
            TF_VAR_project_name=self.project_name,
            TF_VAR_gitlab_token=self.gitlab_private_token,
            TF_VAR_gitlab_project_variables="{%s}"
            % ", ".join(f"{k} = {v}" for k, v in project_variables.items()),
            TF_VAR_project_slug=self.project_slug,
            TF_VAR_service_dir=self.service_dir,
            TF_VAR_service_slug=self.service_slug,
            TF_VAR_terraform_cloud_hostname=self.terraform_cloud_hostname,
            TF_VAR_terraform_cloud_token=self.terraform_cloud_token,
        )
        state_path = terraform_dir / "state.tfstate"
        logs_dir = self.logs_dir / self.service_slug / "terraform"
        os.makedirs(logs_dir)
        init_log_path = logs_dir / "init.log"
        init_stdout_path = logs_dir / "init-stdout.log"
        init_stderr_path = logs_dir / "init-stderr.log"
        cwd = Path(__file__).parent.parent / "terraform"
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
            if apply_process.returncode != 0:
                apply_stderr_path.write_text(apply_process.stderr)
                click.echo(
                    error(
                        "Error applying Terraform GitLab configuration "
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
                            "Error performing Terraform destroy "
                            f"(check {destroy_stderr_path} and {destroy_log_path})"
                        )
                    )
                raise BootstrapError
        else:
            init_stderr_path.write_text(init_process.stderr)
            click.echo(
                error(
                    "Error performing Terraform init "
                    f"(check {init_stderr_path} and {init_log_path})"
                )
            )
            raise BootstrapError

    def run(self):
        """Run the bootstrap."""
        click.echo(highlight(f"Initializing the {self.service_slug} service:"))
        self.init_service()
        self.create_env_file()
        if self.gitlab_group_slug:
            self.init_gitlab()
        if self.terraform_backend == TERRAFORM_BACKEND_TFC:
            self.init_terraform_cloud()
        backend_template_url = BACKEND_TEMPLATE_URLS.get(self.backend_type)
        if backend_template_url:
            self.init_subrepo(
                self.backend_service_slug,
                backend_template_url,
                internal_service_port=self.backend_service_port,
                media_storage=self.media_storage,
                sentry_dsn=self.backend_sentry_dsn,
            )
        frontend_template_url = FRONTEND_TEMPLATE_URLS.get(self.frontend_type)
        if frontend_template_url:
            self.init_subrepo(
                self.frontend_service_slug,
                frontend_template_url,
                internal_backend_url=(
                    f"http://{self.backend_service_slug}:{self.backend_service_port}"
                ),
                internal_service_port=self.frontend_service_port,
                sentry_dsn=self.frontend_sentry_dsn,
            )
        self.change_output_owner()
