"""Run the bootstrap."""

import base64
import os
import re
import secrets
import shutil
import subprocess
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

error = partial(click.style, fg="red")

highlight = partial(click.style, fg="cyan")

info = partial(click.style, dim=True)

warning = partial(click.style, fg="yellow")


class Runner:
    """The bootstrap runner."""

    def __init__(
        self,
        uid,
        gid,
        output_dir,
        project_name,
        project_slug,
        project_dirname,
        service_dir,
        backend_type,
        backend_service_slug,
        backend_service_port,
        frontend_type,
        frontend_service_slug,
        frontend_service_port,
        deployment_type,
        terraform_backend,
        terraform_cloud_hostname,
        terraform_cloud_token,
        digitalocean_token,
        kubernetes_cluster_ca_certificate,
        kubernetes_host,
        kubernetes_token,
        environment_distribution,
        project_domain,
        domain_prefix_dev,
        domain_prefix_stage,
        domain_prefix_prod,
        domain_prefix_monitoring,
        project_url_dev,
        project_url_stage,
        project_url_prod,
        project_url_monitoring,
        letsencrypt_certificate_email,
        digitalocean_create_domain,
        digitalocean_k8s_cluster_region,
        digitalocean_database_cluster_region,
        digitalocean_database_cluster_node_size,
        postgres_image,
        postgres_persistent_volume_capacity,
        postgres_persistent_volume_claim_capacity,
        postgres_persistent_volume_host_path,
        use_redis,
        redis_image,
        digitalocean_redis_cluster_region,
        digitalocean_redis_cluster_node_size,
        sentry_org,
        sentry_url,
        backend_sentry_dsn,
        frontend_sentry_dsn,
        sentry_auth_token,
        pact_broker_url,
        pact_broker_username,
        pact_broker_password,
        media_storage,
        s3_region,
        s3_host,
        s3_access_id,
        s3_secret_key,
        s3_bucket_name,
        gitlab_private_token,
        gitlab_group_slug,
        gitlab_group_owners,
        gitlab_group_maintainers,
        gitlab_group_developers,
        terraform_dir,
        logs_dir,
    ):
        """Initialize the instance."""
        self.uid = uid
        self.gid = gid
        self.output_dir = output_dir
        self.project_name = project_name
        self.project_slug = project_slug
        self.project_dirname = project_dirname
        self.service_dir = service_dir
        self.backend_type = backend_type
        self.backend_service_slug = backend_service_slug
        self.backend_service_port = backend_service_port
        self.frontend_type = frontend_type
        self.frontend_service_slug = frontend_service_slug
        self.frontend_service_port = frontend_service_port
        self.deployment_type = deployment_type
        self.terraform_backend = terraform_backend
        self.terraform_cloud_hostname = terraform_cloud_hostname
        self.terraform_cloud_token = terraform_cloud_token
        self.digitalocean_token = digitalocean_token
        self.kubernetes_cluster_ca_certificate = kubernetes_cluster_ca_certificate
        self.kubernetes_host = kubernetes_host
        self.kubernetes_token = kubernetes_token
        self.environment_distribution = environment_distribution
        self.project_domain = project_domain
        self.domain_prefix_dev = domain_prefix_dev
        self.domain_prefix_stage = domain_prefix_stage
        self.domain_prefix_prod = domain_prefix_prod
        self.domain_prefix_monitoring = domain_prefix_monitoring
        self.project_url_dev = project_url_dev
        self.project_url_stage = project_url_stage
        self.project_url_prod = project_url_prod
        self.project_url_monitoring = project_url_monitoring
        self.letsencrypt_certificate_email = letsencrypt_certificate_email
        self.digitalocean_create_domain = digitalocean_create_domain
        self.digitalocean_k8s_cluster_region = digitalocean_k8s_cluster_region
        self.digitalocean_database_cluster_region = digitalocean_database_cluster_region
        self.digitalocean_database_cluster_node_size = (
            digitalocean_database_cluster_node_size
        )
        self.postgres_image = postgres_image
        self.postgres_persistent_volume_capacity = postgres_persistent_volume_capacity
        self.postgres_persistent_volume_claim_capacity = (
            postgres_persistent_volume_claim_capacity
        )
        self.postgres_persistent_volume_host_path = postgres_persistent_volume_host_path
        self.use_redis = use_redis
        self.redis_image = redis_image
        self.digitalocean_redis_cluster_region = digitalocean_redis_cluster_region
        self.digitalocean_redis_cluster_node_size = digitalocean_redis_cluster_node_size
        self.sentry_org = sentry_org
        self.sentry_url = sentry_url
        self.backend_sentry_dsn = backend_sentry_dsn
        self.frontend_sentry_dsn = frontend_sentry_dsn
        self.sentry_auth_token = sentry_auth_token
        self.pact_broker_url = pact_broker_url
        self.pact_broker_username = pact_broker_username
        self.pact_broker_password = pact_broker_password
        self.media_storage = media_storage
        self.s3_region = s3_region
        self.s3_host = s3_host
        self.s3_access_id = s3_access_id
        self.s3_secret_key = s3_secret_key
        self.s3_bucket_name = s3_bucket_name
        self.gitlab_private_token = gitlab_private_token
        self.gitlab_group_slug = gitlab_group_slug
        self.gitlab_group_owners = gitlab_group_owners
        self.gitlab_group_maintainers = gitlab_group_maintainers
        self.gitlab_group_developers = gitlab_group_developers
        self.terraform_dir = terraform_dir
        self.logs_dir = logs_dir
        self.service_slug = ORCHESTRATOR_SERVICE_SLUG
        self.run_id = f"{time():.0f}"
        self.terraform_dir = str(
            Path(terraform_dir or f".terraform/{self.run_id}").resolve()
        )
        self.logs_dir = str(Path(logs_dir or f".logs/{self.run_id}").resolve())
        self.stacks_environments = self.get_stacks_environments()

    def get_stacks_environments(self):
        """Return a dict with the environments distribution per stack."""
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
            return {"main": {"dev": dev_env, "stage": stage_env, "prod": prod_env}}
        elif self.environment_distribution == "2":
            return {
                "dev": {"dev": dev_env, "stage": stage_env},
                "main": {"prod": prod_env},
            }
        elif self.environment_distribution == "3":
            return {
                "dev": {"dev": dev_env},
                "stage": {"stage": stage_env},
                "main": {"prod": prod_env},
            }
        return {}

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
                "environment_distribution": self.environment_distribution,
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
        gitlab_group_variables = {}
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
            self.backend_service_slug and gitlab_project_variables.update(
                BACKEND_SERVICE_SLUG=f'{{value = "{self.backend_service_slug}"}}'
            )
            self.frontend_service_slug and gitlab_project_variables.update(
                FRONTEND_SERVICE_SLUG=f'{{value = "{self.frontend_service_slug}"}}'
            )
            gitlab_group_variables = {
                f"STACK_SLUG_{i.upper()}": f'{{value = "{k}"}}'
                for k, v in self.stacks_environments.items()
                for i in v
            }
            self.backend_service_slug and gitlab_project_variables.update(
                BACKEND_SERVICE_PORT=f'{{value = "{self.backend_service_port}"}}'
            )
            self.frontend_service_slug and gitlab_project_variables.update(
                FRONTEND_SERVICE_PORT=f'{{value = "{self.frontend_service_port}"}}'
            )
            self.project_domain and gitlab_group_variables.update(
                DOMAIN='{value = "%s"}' % self.project_domain
            )
            self.backend_service_slug and self.frontend_service_slug and (
                gitlab_group_variables.update(
                    INTERNAL_BACKEND_URL='{value = "http://%s:%s"}'
                    % (self.backend_service_slug, self.backend_service_port)
                )
            )
            self.letsencrypt_certificate_email and gitlab_project_variables.update(
                LETSENCRYPT_CERTIFICATE_EMAIL=(
                    f'{{value = "{self.letsencrypt_certificate_email}"}}'
                ),
                SSL_ENABLED='{{value = "true"}}',
            )

            self.use_redis and gitlab_project_variables.update(
                USE_REDIS='{value = "true"}'
            )
            if self.project_url_monitoring:
                gitlab_project_variables.update(
                    MONITORING_URL='{value = "%s"}' % self.project_url_monitoring,
                    GRAFANA_PASSWORD='{value = "%s", masked = true}'
                    % secrets.token_urlsafe(12),
                )
                self.domain_prefix_monitoring and gitlab_project_variables.update(
                    MONITORING_DOMAIN_PREFIX='{value = "%s"}'
                    % self.domain_prefix_monitoring
                )
            self.digitalocean_token and gitlab_group_variables.update(
                DIGITALOCEAN_TOKEN='{value = "%s", masked = true}'
                % self.digitalocean_token
            )
            if "digitalocean" in self.deployment_type:
                gitlab_project_variables.update(
                    CREATE_DOMAIN='{value = "%s"}'
                    % (self.digitalocean_create_domain and "true" or "false"),
                    DIGITALOCEAN_K8S_CLUSTER_REGION='{value = "%s"}'
                    % self.digitalocean_k8s_cluster_region,
                    DIGITALOCEAN_DATABASE_CLUSTER_REGION='{value = "%s"}'
                    % self.digitalocean_database_cluster_region,
                    DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE='{value = "%s"}'
                    % self.digitalocean_database_cluster_node_size,
                )
                self.use_redis and gitlab_project_variables.update(
                    DIGITALOCEAN_REDIS_CLUSTER_REGION='{value = "%s"}'
                    % self.digitalocean_redis_cluster_region,
                    DIGITALOCEAN_REDIS_CLUSTER_NODE_SIZE='{value = "%s"}'
                    % self.digitalocean_redis_cluster_node_size,
                )
            elif self.deployment_type == DEPLOYMENT_TYPE_OTHER:
                gitlab_group_variables.update(
                    KUBERNETES_CLUSTER_CA_CERTIFICATE='{value = "%s", masked = true}'
                    % base64.b64encode(
                        Path(self.kubernetes_cluster_ca_certificate).read_bytes()
                    ).decode(),
                    KUBERNETES_HOST='{value = "%s"}' % self.kubernetes_host,
                    KUBERNETES_TOKEN='{value = "%s", masked = true}'
                    % self.kubernetes_token,
                )
                gitlab_project_variables.update(
                    POSTGRES_IMAGE='{value = "%s"}' % self.postgres_image,
                    POSTGRES_PERSISTENT_VOLUME_CAPACITY='{value = "%s"}'
                    % self.postgres_persistent_volume_capacity,
                    POSTGRES_PERSISTENT_VOLUME_CLAIM_CAPACITY='{value = "%s"}'
                    % self.postgres_persistent_volume_claim_capacity,
                    POSTGRES_PERSISTENT_VOLUME_HOST_PATH='{value = "%s"}'
                    % self.postgres_persistent_volume_host_path,
                )
                self.use_redis and gitlab_project_variables.update(
                    REDIS_IMAGE='{value = "%s"}' % self.redis_image,
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

    def init_gitlab(self):
        """Initialize the GitLab repositories."""
        click.echo(info("...creating the GitLab repository and associated resources"))
        group_variables, project_variables = self.get_gitlab_variables()
        terraform_dir = Path(self.terraform_dir) / self.service_slug
        os.makedirs(terraform_dir, exist_ok=True)
        env = dict(
            PATH=os.environ.get("PATH"),
            TF_DATA_DIR=str((Path(terraform_dir) / "data").resolve()),
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
        state_path = Path(terraform_dir) / "state.tfstate"
        logs_dir = Path(self.logs_dir) / self.service_slug / "terraform"
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
                internal_service_port=self.frontend_service_port,
                sentry_dsn=self.frontend_sentry_dsn,
            )
        self.change_output_owner()
