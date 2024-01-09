"""Collect options to initialize a template based web project."""

from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree

import click
from pydantic import validate_arguments
from slugify import slugify

from bootstrap.constants import (
    AWS_S3_REGION_DEFAULT,
    BACKEND_TYPE_CHOICES,
    BACKEND_TYPE_DEFAULT,
    DEPLOYMENT_TYPE_CHOICES,
    DEPLOYMENT_TYPE_DIGITALOCEAN,
    DEPLOYMENT_TYPE_OTHER,
    DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE_DEFAULT,
    DIGITALOCEAN_REDIS_CLUSTER_NODE_SIZE_DEFAULT,
    DIGITALOCEAN_SPACES_REGION_DEFAULT,
    EMPTY_SERVICE_TYPE,
    ENVIRONMENTS_DISTRIBUTION_CHOICES,
    ENVIRONMENTS_DISTRIBUTION_DEFAULT,
    ENVIRONMENTS_DISTRIBUTION_PROMPT,
    FRONTEND_TYPE_CHOICES,
    FRONTEND_TYPE_DEFAULT,
    GITLAB_URL_DEFAULT,
    MEDIA_STORAGE_AWS_S3,
    MEDIA_STORAGE_CHOICES,
    MEDIA_STORAGE_DIGITALOCEAN_S3,
    TERRAFORM_BACKEND_CHOICES,
    TERRAFORM_BACKEND_TFC,
)
from bootstrap.helpers import (
    validate_or_prompt_domain,
    validate_or_prompt_email,
    validate_or_prompt_path,
    validate_or_prompt_secret,
    validate_or_prompt_url,
    warning,
)
from bootstrap.runner import Runner


@validate_arguments
@dataclass(kw_only=True)
class Collector:
    """The bootstrap CLI options collector."""

    output_dir: Path = Path(".")
    project_name: str | None = None
    project_slug: str | None = None
    project_dirname: str | None = None
    backend_type: str | None = None
    backend_service_slug: str | None = None
    backend_service_port: int | None = None
    frontend_type: str | None = None
    frontend_service_slug: str | None = None
    frontend_service_port: int | None = None
    deployment_type: str | None = None
    terraform_backend: str | None = None
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
    environments_distribution: str | None = None
    project_domain: str | None = None
    subdomain_dev: str | None = None
    subdomain_stage: str | None = None
    subdomain_prod: str | None = None
    subdomain_monitoring: str | None = None
    project_url_dev: str | None = None
    project_url_stage: str | None = None
    project_url_prod: str | None = None
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
    use_redis: bool | None = None
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
    media_storage: str | None = None
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
    quiet: bool = False

    def __post_init__(self):
        """Finalize initialization."""
        self._service_dir = None
        self._digitalocean_enabled = False
        self._other_kubernetes_enabled = False

    def collect(self):
        """Collect options."""
        self.set_project_name()
        self.set_project_slug()
        self.set_project_dirname()
        self.set_service_dir()
        self.set_backend_service()
        self.set_frontend_service()
        self.set_use_redis()
        self.set_terraform()
        self.set_vault()
        self.set_deployment_type()
        self.set_environments_distribution()
        self.set_domain_and_urls()
        self.set_letsencrypt()
        self.set_deployment()
        self.set_sentry()
        self.set_pact()
        self.set_gitlab()
        self.set_storage()

    def set_project_name(self):
        """Set the project name option."""
        self.project_name = self.project_name or click.prompt("Project name")

    def set_project_slug(self):
        """Set the project slug option."""
        self.project_slug = slugify(
            self.project_slug
            or click.prompt("Project slug", default=slugify(self.project_name))
        )

    def set_project_dirname(self):
        """Set the project dirname option."""
        self.project_dirname = slugify(self.project_slug, separator="")

    def set_service_dir(self):
        """Set the service dir option."""
        service_dir = self.output_dir / self.project_dirname
        if service_dir.is_dir() and click.confirm(
            warning(
                f'A directory "{service_dir.resolve()}" already exists and '
                "must be deleted. Continue?",
            ),
            abort=True,
        ):
            rmtree(service_dir)
        self._service_dir = service_dir

    def set_backend_service(self):
        """Set the backend service options."""
        if self.backend_type not in BACKEND_TYPE_CHOICES:
            self.backend_type = click.prompt(
                "Backend type",
                default=BACKEND_TYPE_DEFAULT,
                type=click.Choice(BACKEND_TYPE_CHOICES, case_sensitive=False),
            ).lower()
        if self.backend_type != EMPTY_SERVICE_TYPE:
            self.backend_service_slug = slugify(
                self.backend_service_slug
                or click.prompt("Backend service slug", default="backend"),
                separator="",
            )

    def set_frontend_service(self):
        """Set the frontend service options."""
        if self.frontend_type not in FRONTEND_TYPE_CHOICES:
            self.frontend_type = click.prompt(
                "Frontend type",
                default=FRONTEND_TYPE_DEFAULT,
                type=click.Choice(FRONTEND_TYPE_CHOICES, case_sensitive=False),
            ).lower()
        if self.frontend_type != EMPTY_SERVICE_TYPE:
            self.frontend_service_slug = slugify(
                self.frontend_service_slug
                or click.prompt("Frontend service slug", default="frontend"),
                separator="",
            )

    def set_use_redis(self):
        """Set the use Redis option."""
        if self.use_redis is None:
            self.use_redis = click.confirm(
                warning("Do you want to use Redis?"), default=False
            )

    def set_terraform(self):
        """Set the Terraform options."""
        if self.terraform_backend not in TERRAFORM_BACKEND_CHOICES:
            self.terraform_backend = click.prompt(
                "Terraform backend",
                default=TERRAFORM_BACKEND_TFC,
                type=click.Choice(TERRAFORM_BACKEND_CHOICES, case_sensitive=False),
            ).lower()
        if self.terraform_backend == TERRAFORM_BACKEND_TFC:
            self.set_terraform_cloud()

    def set_terraform_cloud(self):
        """Set the Terraform Cloud options."""
        self.terraform_cloud_hostname = validate_or_prompt_domain(
            "Terraform host name",
            self.terraform_cloud_hostname,
            default="app.terraform.io",
        )
        self.terraform_cloud_token = validate_or_prompt_secret(
            "Terraform Cloud User token", self.terraform_cloud_token
        )
        self.terraform_cloud_organization = (
            self.terraform_cloud_organization or click.prompt("Terraform Organization")
        )
        if self.terraform_cloud_organization_create is None:
            self.terraform_cloud_organization_create = click.confirm(
                "Do you want to create Terraform Cloud Organization "
                f"'{self.terraform_cloud_organization}'?",
            )
        if self.terraform_cloud_organization_create:
            self.terraform_cloud_admin_email = validate_or_prompt_email(
                "Terraform Cloud Organization admin email (e.g. tech@20tab.com)",
                self.terraform_cloud_admin_email,
            )
        else:
            self.terraform_cloud_admin_email = ""

    def set_vault(self):
        """Set the Vault options."""
        if self.vault_url or (
            self.vault_url is None
            and click.confirm("Do you want to use Vault for secrets management?")
        ):
            self.vault_token = validate_or_prompt_secret(
                "Vault token "
                "(leave blank to perform a browser-based OIDC authentication)",
                self.vault_token,
                default="",
                required=False,
            )
            self.quiet or click.confirm(
                warning(
                    "Make sure your Vault permissions allow to enable the "
                    "project secrets backends and manage the project secrets. Continue?"
                ),
                abort=True,
            )
            self.vault_url = validate_or_prompt_url("Vault address", self.vault_url)

    def set_deployment_type(self):
        """Set the deployment type option."""
        if self.deployment_type not in DEPLOYMENT_TYPE_CHOICES:
            self.deployment_type = click.prompt(
                "Deploy type",
                default=DEPLOYMENT_TYPE_DIGITALOCEAN,
                type=click.Choice(DEPLOYMENT_TYPE_CHOICES, case_sensitive=False),
            ).lower()

    def set_environments_distribution(self):
        """Set the environments distribution option."""
        # TODO: forcing a single stack when deployment is `k8s-other` should be removed,
        #       and `set_deployment_type` merged with `set_deployment`
        if self.deployment_type == DEPLOYMENT_TYPE_OTHER:
            self.environments_distribution = "1"
        elif self.environments_distribution not in ENVIRONMENTS_DISTRIBUTION_CHOICES:
            self.environments_distribution = click.prompt(
                ENVIRONMENTS_DISTRIBUTION_PROMPT,
                default=ENVIRONMENTS_DISTRIBUTION_DEFAULT,
                type=click.Choice(ENVIRONMENTS_DISTRIBUTION_CHOICES),
            )

    def set_domain_and_urls(self):
        """Set the domain and urls options."""
        self.project_domain = validate_or_prompt_domain(
            "Project domain", self.project_domain, default=f"{self.project_slug}.com"
        )
        self.subdomain_dev = slugify(
            self.subdomain_dev
            or click.prompt("Development domain prefix", default="dev")
        )
        self.project_url_dev = f"https://{self.subdomain_dev}.{self.project_domain}"
        self.subdomain_stage = slugify(
            self.subdomain_stage
            or click.prompt("Staging domain prefix", default="stage")
        )
        self.project_url_stage = f"https://{self.subdomain_stage}.{self.project_domain}"
        self.subdomain_prod = slugify(
            self.subdomain_prod
            or click.prompt("Production domain prefix", default="www")
        )
        self.project_url_prod = f"https://{self.subdomain_prod}.{self.project_domain}"
        if self.subdomain_monitoring is not None or click.confirm(
            warning("Do you want to enable the monitoring stack?"), default=False
        ):
            self.subdomain_monitoring = slugify(
                self.subdomain_monitoring
                or click.prompt("Monitoring domain prefix", default="logs")
            )

    def set_letsencrypt(self):
        """Set Let's Encrypt options."""
        self.letsencrypt_certificate_email = (
            self.letsencrypt_certificate_email
            or (
                self.letsencrypt_certificate_email is None
                and click.confirm(
                    warning("Do you want Traefik to generate SSL certificates?"),
                    default=True,
                )
                and validate_or_prompt_email(
                    "Let's Encrypt certificates email",
                    self.letsencrypt_certificate_email,
                )
            )
            or None
        )

    def set_deployment(self):
        """Set the deployment options."""
        if "digitalocean" in self.deployment_type:
            self.set_digitalocean()
        elif self.deployment_type == DEPLOYMENT_TYPE_OTHER:
            self.set_kubernetes()
        else:
            raise ValueError("Invalid deployment type.")

    def set_digitalocean(self):
        """Set the DigitalOcean options."""
        self._digitalocean_enabled = True
        self.set_digitalocean_token()
        # TODO: these settings should be different for each stack
        if self.digitalocean_domain_create is None:
            self.digitalocean_domain_create = click.confirm(
                "Do you want to create the DigitalOcean domain?", default=True
            )
        if self.digitalocean_dns_records_create is None:
            self.digitalocean_dns_records_create = click.confirm(
                "Do you want to create DigitalOcean DNS records?", default=True
            )
        self.digitalocean_k8s_cluster_region = (
            self.digitalocean_k8s_cluster_region
            or click.prompt("Kubernetes cluster DigitalOcean region", default="fra1")
        )
        self.digitalocean_database_cluster_region = (
            self.digitalocean_database_cluster_region
            or click.prompt("Database cluster DigitalOcean region", default="fra1")
        )
        self.digitalocean_database_cluster_node_size = (
            self.digitalocean_database_cluster_node_size
            or click.prompt(
                "Database cluster node size",
                default=DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE_DEFAULT,
            )
        )
        if self.use_redis:
            if self.digitalocean_redis_cluster_region is None:
                self.digitalocean_redis_cluster_region = click.prompt(
                    "Redis cluster DigitalOcean region", default="fra1"
                )
            if self.digitalocean_redis_cluster_node_size is None:
                self.digitalocean_redis_cluster_node_size = click.prompt(
                    "Redis cluster node size",
                    default=DIGITALOCEAN_REDIS_CLUSTER_NODE_SIZE_DEFAULT,
                )

    def set_digitalocean_token(self):
        """Set the DigitalOcean token option."""
        self.digitalocean_token = validate_or_prompt_secret(
            "DigitalOcean token", self.digitalocean_token
        )

    def set_kubernetes(self):
        """Set the Kubernetes options."""
        self._other_kubernetes_enabled = True
        # TODO: these settings should be different for each stack
        self.kubernetes_cluster_ca_certificate = (
            self.kubernetes_cluster_ca_certificate
            or click.prompt(
                "Kubernetes cluster CA certificate",
                type=click.Path(dir_okay=False, exists=True, resolve_path=True),
            )
        )
        self.kubernetes_host = self.kubernetes_host or validate_or_prompt_url(
            "Kubernetes host", self.kubernetes_host
        )
        self.kubernetes_token = self.kubernetes_token or validate_or_prompt_secret(
            "Kubernetes token", self.kubernetes_token
        )
        self.postgres_image = self.postgres_image or click.prompt(
            "Postgres Docker image", default="postgres:14"
        )
        self.postgres_persistent_volume_capacity = (
            self.postgres_persistent_volume_capacity
            or click.prompt("Postgres K8s PersistentVolume capacity", default="10Gi")
        )
        self.postgres_persistent_volume_claim_capacity = (
            self.postgres_persistent_volume_claim_capacity or ""
        )
        self.postgres_persistent_volume_host_path = (
            self.postgres_persistent_volume_host_path
            or click.prompt("Postgres K8s PersistentVolume host path")
        )
        if self.use_redis:
            self.redis_image = self.redis_image or click.prompt(
                "Redis Docker image", default="redis:6.2"
            )
        else:
            self.redis_image = ""

    def set_sentry(self):
        """Set the Sentry options."""
        if any((self.backend_service_slug, self.frontend_service_slug)) and (
            self.sentry_org
            or (
                self.sentry_org is None
                and click.confirm(warning("Do you want to use Sentry?"), default=False)
            )
        ):
            self.sentry_org = self.sentry_org or click.prompt("Sentry organization")
            self.sentry_url = validate_or_prompt_url(
                "Sentry URL", self.sentry_url, default="https://sentry.io/"
            )
            self.sentry_auth_token = validate_or_prompt_secret(
                "Sentry auth token", self.sentry_auth_token
            )
            self.backend_sentry_dsn = self.backend_sentry_dsn or validate_or_prompt_url(
                f"Sentry DSN of the {self.backend_service_slug} service (leave blank if unused)",
                self.backend_sentry_dsn,
                default="",
                required=False,
            )
            self.frontend_sentry_dsn = self.frontend_sentry_dsn or validate_or_prompt_url(
                f"Sentry DSN of the {self.frontend_service_slug} service (leave blank if unused)",
                self.frontend_sentry_dsn,
                default="",
                required=False,
            )

    def set_pact(self):
        """Set the Pact options."""
        if self.pact_broker_url or (
            self.pact_broker_url is None
            and click.confirm(warning("Do you want to use Pact?"), default=False)
        ):
            self.pact_broker_url = validate_or_prompt_url(
                "Pact broker URL (e.g. https://broker.20tab.com/)", self.pact_broker_url
            )
            self.pact_broker_username = self.pact_broker_username or click.prompt(
                "Pact broker username",
            )
            self.pact_broker_password = validate_or_prompt_secret(
                "Pact broker password", self.pact_broker_password
            )

    def set_gitlab(self):
        """Set the GitLab options."""
        if self.gitlab_url or (
            self.gitlab_url is None
            and click.confirm(warning("Do you want to use GitLab?"), default=True)
        ):
            self.gitlab_url = validate_or_prompt_url(
                "GitLab URL", self.gitlab_url, default=GITLAB_URL_DEFAULT
            )
            self.gitlab_token = self.gitlab_token or click.prompt(
                "GitLab access token (with API scope enabled)", hide_input=True
            )
            self.gitlab_namespace_path = validate_or_prompt_path(
                "GitLab parent group path (leave blank for a root level group)",
                self.gitlab_namespace_path,
                default="",
                required=False,
            ).strip("/")
            self.gitlab_group_slug = slugify(
                self.gitlab_group_slug
                or click.prompt("GitLab group slug", default=self.project_slug)
            )
            self.quiet or (
                self.gitlab_namespace_path == ""
                and self.gitlab_url == GITLAB_URL_DEFAULT
                and click.confirm(
                    warning(
                        f'Make sure the GitLab "{self.gitlab_group_slug}" group exists '
                        "before proceeding. Continue?"
                    ),
                    abort=True,
                )
            )
            if self.gitlab_group_owners is None:
                self.gitlab_group_owners = click.prompt(
                    "Comma-separated GitLab group owners", default=""
                )
            if self.gitlab_group_maintainers is None:
                self.gitlab_group_maintainers = click.prompt(
                    "Comma-separated GitLab group maintainers", default=""
                )
            if self.gitlab_group_developers is None:
                self.gitlab_group_developers = click.prompt(
                    "Comma-separated GitLab group developers", default=""
                )

    def set_storage(self):
        """Set the storage options."""
        if self.media_storage is None:
            self.media_storage = click.prompt(
                "Media storage",
                default=MEDIA_STORAGE_DIGITALOCEAN_S3,
                type=click.Choice(MEDIA_STORAGE_CHOICES, case_sensitive=False),
            ).lower()
        if self.media_storage == MEDIA_STORAGE_DIGITALOCEAN_S3:
            self.set_digitalocean_spaces()
        elif self.media_storage == MEDIA_STORAGE_AWS_S3:
            self.set_aws_s3()
        if "s3" in self.media_storage:
            self.s3_access_id = validate_or_prompt_secret(
                "S3 Access Key ID", self.s3_access_id
            )
            self.s3_secret_key = validate_or_prompt_secret(
                "S3 Secret Access Key", self.s3_secret_key
            )

    def set_digitalocean_spaces(self):
        """Set the DigitalOcean Spaces options."""
        self.set_digitalocean_token()
        self.digitalocean_token = validate_or_prompt_secret(
            "DigitalOcean token", self.digitalocean_token
        )
        self.s3_region = self.s3_region or click.prompt(
            "DigitalOcean Spaces region",
            default=DIGITALOCEAN_SPACES_REGION_DEFAULT,
        )
        self.s3_host = "digitaloceanspaces.com"
        self.s3_bucket_name = ""

    def set_aws_s3(self):
        """Set the AWS S3 options."""
        self.s3_region = self.s3_region or click.prompt(
            "AWS S3 region name",
            default=AWS_S3_REGION_DEFAULT,
        )
        self.s3_host = ""
        self.s3_bucket_name = self.s3_bucket_name or click.prompt(
            "AWS S3 bucket name",
        )

    def get_runner(self):
        """Get the bootstrap runner instance."""
        return Runner(
            uid=self.uid,
            gid=self.gid,
            output_dir=self.output_dir,
            project_name=self.project_name,
            project_slug=self.project_slug,
            project_dirname=self.project_dirname,
            service_dir=self._service_dir,
            backend_type=self.backend_type,
            backend_service_slug=self.backend_service_slug,
            backend_service_port=self.backend_service_port,
            frontend_type=self.frontend_type,
            frontend_service_slug=self.frontend_service_slug,
            frontend_service_port=self.frontend_service_port,
            deployment_type=self.deployment_type,
            terraform_backend=self.terraform_backend,
            terraform_cloud_hostname=self.terraform_cloud_hostname,
            terraform_cloud_token=self.terraform_cloud_token,
            terraform_cloud_organization=self.terraform_cloud_organization,
            terraform_cloud_organization_create=self.terraform_cloud_organization_create,
            terraform_cloud_admin_email=self.terraform_cloud_admin_email,
            vault_token=self.vault_token,
            vault_url=self.vault_url,
            digitalocean_token=self.digitalocean_token,
            kubernetes_cluster_ca_certificate=self.kubernetes_cluster_ca_certificate,
            kubernetes_host=self.kubernetes_host,
            kubernetes_token=self.kubernetes_token,
            environments_distribution=self.environments_distribution,
            project_domain=self.project_domain,
            subdomain_dev=self.subdomain_dev,
            subdomain_stage=self.subdomain_stage,
            subdomain_prod=self.subdomain_prod,
            subdomain_monitoring=self.subdomain_monitoring,
            project_url_dev=self.project_url_dev,
            project_url_stage=self.project_url_stage,
            project_url_prod=self.project_url_prod,
            letsencrypt_certificate_email=self.letsencrypt_certificate_email,
            digitalocean_domain_create=self.digitalocean_domain_create,
            digitalocean_dns_records_create=self.digitalocean_dns_records_create,
            digitalocean_k8s_cluster_region=self.digitalocean_k8s_cluster_region,
            digitalocean_database_cluster_region=self.digitalocean_database_cluster_region,
            digitalocean_database_cluster_node_size=self.digitalocean_database_cluster_node_size,
            postgres_image=self.postgres_image,
            postgres_persistent_volume_capacity=self.postgres_persistent_volume_capacity,
            postgres_persistent_volume_claim_capacity=self.postgres_persistent_volume_claim_capacity,
            postgres_persistent_volume_host_path=self.postgres_persistent_volume_host_path,
            use_redis=self.use_redis,
            redis_image=self.redis_image,
            digitalocean_redis_cluster_region=self.digitalocean_redis_cluster_region,
            digitalocean_redis_cluster_node_size=self.digitalocean_redis_cluster_node_size,
            sentry_org=self.sentry_org,
            sentry_url=self.sentry_url,
            backend_sentry_dsn=self.backend_sentry_dsn,
            frontend_sentry_dsn=self.frontend_sentry_dsn,
            sentry_auth_token=self.sentry_auth_token,
            pact_broker_url=self.pact_broker_url,
            pact_broker_username=self.pact_broker_username,
            pact_broker_password=self.pact_broker_password,
            media_storage=self.media_storage,
            s3_region=self.s3_region,
            s3_host=self.s3_host,
            s3_access_id=self.s3_access_id,
            s3_secret_key=self.s3_secret_key,
            s3_bucket_name=self.s3_bucket_name,
            gitlab_url=self.gitlab_url,
            gitlab_token=self.gitlab_token,
            gitlab_namespace_path=self.gitlab_namespace_path,
            gitlab_group_slug=self.gitlab_group_slug,
            gitlab_group_owners=self.gitlab_group_owners,
            gitlab_group_maintainers=self.gitlab_group_maintainers,
            gitlab_group_developers=self.gitlab_group_developers,
            terraform_dir=self.terraform_dir,
            logs_dir=self.logs_dir,
        )

    def launch_runner(self):
        """Launch a bootstrap runner with the collected options."""
        self.get_runner().run()
