"""Collect options to initialize a template based web project."""

import shutil
from functools import partial
from pathlib import Path

import click
import validators
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
    ENVIRONMENT_DISTRIBUTION_CHOICES,
    ENVIRONMENT_DISTRIBUTION_DEFAULT,
    ENVIRONMENT_DISTRIBUTION_PROMPT,
    FRONTEND_TYPE_CHOICES,
    FRONTEND_TYPE_DEFAULT,
    MEDIA_STORAGE_AWS_S3,
    MEDIA_STORAGE_CHOICES,
    MEDIA_STORAGE_DIGITALOCEAN_S3,
)

error = partial(click.style, fg="red")

warning = partial(click.style, fg="yellow")


def collect(
    uid,
    gid,
    output_dir,
    project_name,
    project_slug,
    project_dirname,
    backend_type,
    backend_service_slug,
    backend_service_port,
    frontend_type,
    frontend_service_slug,
    frontend_service_port,
    deployment_type,
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
    quiet,
):
    """Collect options and run the bootstrap."""
    project_slug = clean_project_slug(project_name, project_slug)
    project_dirname = slugify(project_slug, separator="")
    service_dir = clean_service_dir(output_dir, project_dirname)
    if (backend_type := clean_backend_type(backend_type)) != EMPTY_SERVICE_TYPE:
        backend_service_slug = clean_backend_service_slug(backend_service_slug)
    if (frontend_type := clean_frontend_type(frontend_type)) != EMPTY_SERVICE_TYPE:
        frontend_service_slug = clean_frontend_service_slug(frontend_service_slug)
    deployment_type = clean_deployment_type(deployment_type)
    environment_distribution = clean_environment_distribution(
        environment_distribution, deployment_type
    )
    use_monitoring = click.confirm(
        warning("Do you want to enable the monitoring stack?"), default=False
    )
    # The "digitalocean-k8s" deployment type includes Postgres by default
    if digitalocean_enabled := ("digitalocean" in deployment_type):
        digitalocean_token = validate_or_prompt_password(
            "DigitalOcean token", digitalocean_token, required=True
        )
    if other_kubernetes_enabled := (deployment_type == DEPLOYMENT_TYPE_OTHER):
        (
            kubernetes_cluster_ca_certificate,
            kubernetes_host,
            kubernetes_token,
        ) = clean_kubernetes_credentials(
            kubernetes_cluster_ca_certificate,
            kubernetes_host,
            kubernetes_token,
        )
    (
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
    ) = clean_project_urls(
        deployment_type,
        project_slug,
        project_domain,
        use_monitoring,
        domain_prefix_dev,
        domain_prefix_stage,
        domain_prefix_prod,
        domain_prefix_monitoring,
        project_url_dev,
        project_url_stage,
        project_url_prod,
        project_url_monitoring,
        letsencrypt_certificate_email,
    )
    use_redis = click.confirm(warning("Do you want to use Redis?"), default=False)
    if digitalocean_enabled:
        (
            digitalocean_create_domain,
            digitalocean_k8s_cluster_region,
            digitalocean_database_cluster_region,
            digitalocean_database_cluster_node_size,
            digitalocean_redis_cluster_region,
            digitalocean_redis_cluster_node_size,
        ) = clean_digitalocean_options(
            project_domain,
            digitalocean_create_domain,
            digitalocean_k8s_cluster_region,
            digitalocean_database_cluster_region,
            digitalocean_database_cluster_node_size,
            digitalocean_redis_cluster_region,
            digitalocean_redis_cluster_node_size,
            use_redis,
        )
    if other_kubernetes_enabled:
        (
            postgres_image,
            postgres_persistent_volume_capacity,
            postgres_persistent_volume_claim_capacity,
            postgres_persistent_volume_host_path,
            redis_image,
        ) = clean_other_k8s_options(
            postgres_image,
            postgres_persistent_volume_capacity,
            postgres_persistent_volume_claim_capacity,
            postgres_persistent_volume_host_path,
            redis_image,
            use_redis,
        )
    media_storage = clean_media_storage(media_storage)
    (
        sentry_org,
        sentry_url,
        sentry_auth_token,
        backend_sentry_dsn,
        frontend_sentry_dsn,
    ) = clean_sentry_data(
        sentry_org,
        sentry_url,
        sentry_auth_token,
        backend_type,
        backend_sentry_dsn,
        frontend_type,
        frontend_sentry_dsn,
    )
    (
        pact_broker_url,
        pact_broker_username,
        pact_broker_password,
    ) = clean_pact_broker_data(
        pact_broker_url, pact_broker_username, pact_broker_password
    )
    (
        gitlab_group_slug,
        gitlab_private_token,
        gitlab_group_owners,
        gitlab_group_maintainers,
        gitlab_group_developers,
    ) = clean_gitlab_group_data(
        project_slug,
        gitlab_group_slug,
        gitlab_private_token,
        gitlab_group_owners,
        gitlab_group_maintainers,
        gitlab_group_developers,
        quiet,
    )
    if gitlab_group_slug and "s3" in media_storage:
        (
            digitalocean_token,
            s3_region,
            s3_host,
            s3_access_id,
            s3_secret_key,
            s3_bucket_name,
        ) = clean_s3_media_storage_data(
            media_storage,
            digitalocean_token,
            s3_region,
            s3_host,
            s3_access_id,
            s3_secret_key,
            s3_bucket_name,
        )
    return {
        "uid": uid,
        "gid": gid,
        "output_dir": output_dir,
        "project_name": project_name,
        "project_slug": project_slug,
        "project_dirname": project_dirname,
        "service_dir": service_dir,
        "backend_type": backend_type,
        "backend_service_slug": backend_service_slug,
        "backend_service_port": backend_service_port,
        "frontend_type": frontend_type,
        "frontend_service_slug": frontend_service_slug,
        "frontend_service_port": frontend_service_port,
        "deployment_type": deployment_type,
        "digitalocean_token": digitalocean_token,
        "kubernetes_cluster_ca_certificate": kubernetes_cluster_ca_certificate,
        "kubernetes_host": kubernetes_host,
        "kubernetes_token": kubernetes_token,
        "environment_distribution": environment_distribution,
        "project_domain": project_domain,
        "domain_prefix_dev": domain_prefix_dev,
        "domain_prefix_stage": domain_prefix_stage,
        "domain_prefix_prod": domain_prefix_prod,
        "domain_prefix_monitoring": domain_prefix_monitoring,
        "project_url_dev": project_url_dev,
        "project_url_stage": project_url_stage,
        "project_url_prod": project_url_prod,
        "project_url_monitoring": project_url_monitoring,
        "letsencrypt_certificate_email": letsencrypt_certificate_email,
        "digitalocean_create_domain": digitalocean_create_domain,
        "digitalocean_k8s_cluster_region": digitalocean_k8s_cluster_region,
        "digitalocean_database_cluster_region": digitalocean_database_cluster_region,
        "digitalocean_database_cluster_node_size": (
            digitalocean_database_cluster_node_size
        ),
        "postgres_image": postgres_image,
        "postgres_persistent_volume_capacity": postgres_persistent_volume_capacity,
        "postgres_persistent_volume_claim_capacity": (
            postgres_persistent_volume_claim_capacity
        ),
        "postgres_persistent_volume_host_path": postgres_persistent_volume_host_path,
        "use_redis": use_redis,
        "redis_image": redis_image,
        "digitalocean_redis_cluster_region": digitalocean_redis_cluster_region,
        "digitalocean_redis_cluster_node_size": digitalocean_redis_cluster_node_size,
        "sentry_org": sentry_org,
        "sentry_url": sentry_url,
        "backend_sentry_dsn": backend_sentry_dsn,
        "frontend_sentry_dsn": frontend_sentry_dsn,
        "sentry_auth_token": sentry_auth_token,
        "pact_broker_url": pact_broker_url,
        "pact_broker_username": pact_broker_username,
        "pact_broker_password": pact_broker_password,
        "media_storage": media_storage,
        "s3_region": s3_region,
        "s3_host": s3_host,
        "s3_access_id": s3_access_id,
        "s3_secret_key": s3_secret_key,
        "s3_bucket_name": s3_bucket_name,
        "gitlab_private_token": gitlab_private_token,
        "gitlab_group_slug": gitlab_group_slug,
        "gitlab_group_owners": gitlab_group_owners,
        "gitlab_group_maintainers": gitlab_group_maintainers,
        "gitlab_group_developers": gitlab_group_developers,
        "terraform_dir": terraform_dir,
        "logs_dir": logs_dir,
    }


def validate_or_prompt_domain(message, value=None, default=None, required=False):
    """Validate the given domain or prompt until a valid value is provided."""
    if value is None:
        value = click.prompt(message, default=default)
    try:
        if not required and value == "" or validators.domain(value):
            return value
    except validators.ValidationFailure:
        pass
    click.echo(error("Please type a valid domain!"))
    return validate_or_prompt_domain(message, None, default, required)


def validate_or_prompt_email(message, value=None, default=None, required=False):
    """Validate the given email address or prompt until a valid value is provided."""
    if value is None:
        value = click.prompt(message, default=default)
    try:
        if not required and value == "" or validators.email(value):
            return value
    except validators.ValidationFailure:
        pass
    click.echo(error("Please type a valid email!"))
    return validate_or_prompt_email(message, None, default, required)


def validate_or_prompt_url(message, value=None, default=None, required=False):
    """Validate the given URL or prompt until a valid value is provided."""
    if value is None:
        value = click.prompt(message, default=default)
    try:
        if not required and value == "" or validators.url(value):
            return value.strip("/")
    except validators.ValidationFailure:
        pass
    click.echo(error("Please type a valid URL!"))
    return validate_or_prompt_url(message, None, default, required)


def validate_or_prompt_password(message, value=None, default=None, required=False):
    """Validate the given password or prompt until a valid value is provided."""
    if value is None:
        value = click.prompt(message, default=default, hide_input=True)
    try:
        if not required and value == "" or validators.length(value, min=8):
            return value
    except validators.ValidationFailure:
        pass
    click.echo(error("Please type at least 8 chars!"))
    return validate_or_prompt_password(message, None, default, required)


def clean_project_slug(project_name, project_slug):
    """Return the project slug."""
    return slugify(
        project_slug or click.prompt("Project slug", default=slugify(project_name))
    )


def clean_service_dir(output_dir, project_dirname):
    """Return the service directory."""
    service_dir = str((Path(output_dir) / project_dirname).resolve())
    if Path(service_dir).is_dir() and click.confirm(
        warning(
            f'A directory "{service_dir}" already exists and '
            "must be deleted. Continue?",
        ),
        abort=True,
    ):
        shutil.rmtree(service_dir)
    return service_dir


def clean_backend_type(backend_type):
    """Return the back end type."""
    return (
        backend_type in BACKEND_TYPE_CHOICES
        and backend_type
        or click.prompt(
            "Backend type",
            default=BACKEND_TYPE_DEFAULT,
            type=click.Choice(BACKEND_TYPE_CHOICES, case_sensitive=False),
        )
    ).lower()


def clean_backend_service_slug(backend_service_slug):
    """Return the back end service slug."""
    return slugify(
        backend_service_slug or click.prompt("Backend service slug", default="backend"),
        separator="",
    )


def clean_frontend_type(frontend_type):
    """Return the front end type."""
    return (
        frontend_type
        if frontend_type in FRONTEND_TYPE_CHOICES
        else click.prompt(
            "Frontend type",
            default=FRONTEND_TYPE_DEFAULT,
            type=click.Choice(FRONTEND_TYPE_CHOICES, case_sensitive=False),
        )
    ).lower()


def clean_frontend_service_slug(frontend_service_slug):
    """Return the front end service slug."""
    return slugify(
        frontend_service_slug
        or click.prompt("Frontend service slug", default="frontend"),
        separator="",
    )


def clean_deployment_type(deployment_type):
    """Return the deployment type."""
    return (
        deployment_type
        if deployment_type in DEPLOYMENT_TYPE_CHOICES
        else click.prompt(
            "Deploy type",
            default=DEPLOYMENT_TYPE_DIGITALOCEAN,
            type=click.Choice(DEPLOYMENT_TYPE_CHOICES, case_sensitive=False),
        )
    ).lower()


def clean_environment_distribution(environment_distribution, deployment_type):
    """Return the environment distribution."""
    if deployment_type == DEPLOYMENT_TYPE_OTHER:
        return "1"
    return (
        environment_distribution
        if environment_distribution in ENVIRONMENT_DISTRIBUTION_CHOICES
        else click.prompt(
            ENVIRONMENT_DISTRIBUTION_PROMPT,
            default=ENVIRONMENT_DISTRIBUTION_DEFAULT,
            type=click.Choice(ENVIRONMENT_DISTRIBUTION_CHOICES),
        )
    )


def clean_kubernetes_credentials(
    kubernetes_cluster_ca_certificate,
    kubernetes_host,
    kubernetes_token,
):
    """Return the clean Kubernetes credentials."""
    kubernetes_cluster_ca_certificate = (
        kubernetes_cluster_ca_certificate
        or click.prompt(
            "Kubernetes cluster CA certificate",
            type=click.Path(dir_okay=False, exists=True, resolve_path=True),
        )
    )
    kubernetes_host = kubernetes_host or validate_or_prompt_url(
        "Kubernetes host", kubernetes_host
    )
    kubernetes_token = kubernetes_token or validate_or_prompt_password(
        "Kubernetes token", kubernetes_token
    )

    return kubernetes_cluster_ca_certificate, kubernetes_host, kubernetes_token


def clean_project_domain(project_domain):
    """Return the project domain."""
    return (
        project_domain
        or (
            project_domain is None
            and click.confirm(
                warning(
                    "Do you want to configure DNS records? "
                    "(BEWARE: NS must be set accordingly)"
                )
            )
            and validate_or_prompt_domain(
                "Project domain", project_domain, required=True
            )
        )
        or ""
    )


def clean_project_urls(
    deployment_type,
    project_slug,
    project_domain,
    use_monitoring,
    domain_prefix_dev,
    domain_prefix_stage,
    domain_prefix_prod,
    domain_prefix_monitoring,
    project_url_dev,
    project_url_stage,
    project_url_prod,
    project_url_monitoring,
    letsencrypt_certificate_email,
):
    """Return project URLs."""
    if deployment_type == DEPLOYMENT_TYPE_DIGITALOCEAN and (
        project_domain := clean_project_domain(project_domain)
    ):
        domain_prefix_dev = domain_prefix_dev or click.prompt(
            "Development domain prefix", default="dev"
        )
        project_url_dev = f"https://{domain_prefix_dev}.{project_domain}"
        domain_prefix_stage = domain_prefix_stage or click.prompt(
            "Staging domain prefix", default="stage"
        )
        project_url_stage = f"https://{domain_prefix_stage}.{project_domain}"
        domain_prefix_prod = domain_prefix_prod or click.prompt(
            "Production domain prefix", default="www"
        )
        project_url_prod = f"https://{domain_prefix_prod}.{project_domain}"
        if use_monitoring:
            domain_prefix_monitoring = domain_prefix_monitoring or click.prompt(
                "Monitorng domain prefix", default="logs"
            )
            project_url_monitoring = (
                f"https://{domain_prefix_monitoring}.{project_domain}"
            )
        else:
            domain_prefix_monitoring = ""
            project_url_monitoring = ""
        letsencrypt_certificate_email = ""
    else:
        project_domain = ""
        domain_prefix_dev = ""
        domain_prefix_stage = ""
        domain_prefix_prod = ""
        domain_prefix_monitoring = ""
        project_url_dev = validate_or_prompt_url(
            "Development environment complete URL",
            project_url_dev or None,
            default=f"https://dev.{project_slug}.com",
        )
        project_url_stage = validate_or_prompt_url(
            "Staging environment complete URL",
            project_url_stage or None,
            default=f"https://stage.{project_slug}.com",
        )
        project_url_prod = validate_or_prompt_url(
            "Production environment complete URL",
            project_url_prod or None,
            default=f"https://www.{project_slug}.com",
        )
        if use_monitoring:
            project_url_monitoring = validate_or_prompt_url(
                "Monitoring complete URL",
                project_url_monitoring or None,
                default=f"https://logs.{project_slug}.com",
            )
        else:
            project_url_monitoring = ""
        letsencrypt_certificate_email = clean_letsencrypt_certificate_email(
            letsencrypt_certificate_email
        )
    return (
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
    )


def clean_letsencrypt_certificate_email(letsencrypt_certificate_email):
    """Return the email to issue Let's Encrypt certificates for."""
    return (
        letsencrypt_certificate_email
        or (
            letsencrypt_certificate_email is None
            and click.confirm(
                warning("Do you want Traefik to generate SSL certificates?"),
                default=True,
            )
            and validate_or_prompt_email(
                "Let's Encrypt certificates email",
                letsencrypt_certificate_email,
                required=True,
            )
        )
        or ""
    )


def clean_sentry_data(
    sentry_org,
    sentry_url,
    sentry_auth_token,
    backend_type,
    backend_sentry_dsn,
    frontend_type,
    frontend_sentry_dsn,
):
    """Return the Sentry configuration data."""
    if sentry_org or (
        sentry_org is None
        and click.confirm(warning("Do you want to use Sentry?"), default=False)
    ):
        sentry_org = clean_sentry_org(sentry_org)
        sentry_url = validate_or_prompt_url(
            "Sentry URL", sentry_url, default="https://sentry.io/", required=True
        )
        sentry_auth_token = validate_or_prompt_password(
            "Sentry auth token", sentry_auth_token, required=True
        )
        backend_sentry_dsn = clean_backend_sentry_dsn(backend_type, backend_sentry_dsn)
        frontend_sentry_dsn = clean_frontend_sentry_dsn(
            frontend_type, frontend_sentry_dsn
        )
    else:
        sentry_org = ""
        sentry_url = ""
        sentry_auth_token = ""
        backend_sentry_dsn = ""
        frontend_sentry_dsn = ""
    return (
        sentry_org,
        sentry_url,
        sentry_auth_token,
        backend_sentry_dsn,
        frontend_sentry_dsn,
    )


def clean_sentry_org(sentry_org):
    """Return the Sentry organization."""
    return (
        sentry_org
        if sentry_org is not None
        else click.prompt("Sentry organization", default="")
    )


def clean_backend_sentry_dsn(backend_type, backend_sentry_dsn):
    """Return the backend Sentry DSN."""
    if backend_type:
        return (
            backend_sentry_dsn
            if backend_sentry_dsn is not None
            else click.prompt(
                "Backend Sentry DSN (leave blank if unused)",
                default="",
            )
        )


def clean_frontend_sentry_dsn(frontend_type, frontend_sentry_dsn):
    """Return the frontend Sentry DSN."""
    if frontend_type:
        return (
            frontend_sentry_dsn
            if frontend_sentry_dsn is not None
            else click.prompt(
                "Frontend Sentry DSN (leave blank if unused)",
                default="",
            )
        )


def clean_digitalocean_options(
    project_domain,
    digitalocean_create_domain,
    digitalocean_k8s_cluster_region,
    digitalocean_database_cluster_region,
    digitalocean_database_cluster_node_size,
    digitalocean_redis_cluster_region,
    digitalocean_redis_cluster_node_size,
    use_redis,
):
    """Return DigitalOcean configuration options."""
    # TODO: ask these settings for each stack
    if project_domain:
        digitalocean_create_domain = (
            digitalocean_create_domain
            if digitalocean_create_domain is not None
            else click.confirm(
                f"Do you want to create DigitalOcean domain '{project_domain}'?",
                default=True,
            )
        )
    else:
        digitalocean_create_domain = None
    digitalocean_k8s_cluster_region = digitalocean_k8s_cluster_region or click.prompt(
        "Kubernetes cluster DigitalOcean region", default="fra1"
    )
    digitalocean_database_cluster_region = (
        digitalocean_database_cluster_region
        or click.prompt("Database cluster DigitalOcean region", default="fra1")
    )
    digitalocean_database_cluster_node_size = (
        digitalocean_database_cluster_node_size
        or click.prompt(
            "Database cluster node size",
            default=DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE_DEFAULT,
        )
    )
    if use_redis:
        digitalocean_redis_cluster_region = (
            digitalocean_redis_cluster_region
            if digitalocean_redis_cluster_region is not None
            else click.prompt("Redis cluster DigitalOcean region", default="fra1")
        )
        digitalocean_redis_cluster_node_size = (
            digitalocean_redis_cluster_node_size
            if digitalocean_redis_cluster_node_size is not None
            else click.prompt(
                "Redis cluster node size",
                default=DIGITALOCEAN_REDIS_CLUSTER_NODE_SIZE_DEFAULT,
            )
        )
    return (
        digitalocean_create_domain,
        digitalocean_k8s_cluster_region,
        digitalocean_database_cluster_region,
        digitalocean_database_cluster_node_size,
        digitalocean_redis_cluster_region,
        digitalocean_redis_cluster_node_size,
    )


def clean_other_k8s_options(
    postgres_image,
    postgres_persistent_volume_capacity,
    postgres_persistent_volume_claim_capacity,
    postgres_persistent_volume_host_path,
    redis_image,
    use_redis,
):
    """Return the Kubernetes custom deployment options."""
    # TODO: ask these settings for each stack
    postgres_image = postgres_image or click.prompt(
        "Postgres Docker image", default="postgres:14"
    )
    postgres_persistent_volume_capacity = (
        postgres_persistent_volume_capacity
        or click.prompt("Postgres K8s PersistentVolume capacity", default="10Gi")
    )
    postgres_persistent_volume_claim_capacity = (
        postgres_persistent_volume_claim_capacity or ""
    )
    postgres_persistent_volume_host_path = (
        postgres_persistent_volume_host_path
        or click.prompt("Postgres K8s PersistentVolume host path")
    )
    if use_redis:
        redis_image = redis_image or click.prompt(
            "Redis Docker image", default="redis:6.2"
        )
    else:
        redis_image = ""
    return (
        postgres_image,
        postgres_persistent_volume_capacity,
        postgres_persistent_volume_claim_capacity,
        postgres_persistent_volume_host_path,
        redis_image,
    )


def clean_pact_broker_data(pact_broker_url, pact_broker_username, pact_broker_password):
    """Return Pact broker data."""
    if pact_broker_url or (
        pact_broker_url is None
        and click.confirm(warning("Do you want to use Pact?"), default=False)
    ):
        pact_broker_url = validate_or_prompt_url(
            "Pact broker URL (e.g. https://broker.20tab.com/)",
            pact_broker_url,
            required=True,
        )
        pact_broker_username = pact_broker_username or click.prompt(
            "Pact broker username",
        )
        pact_broker_password = validate_or_prompt_password(
            "Pact broker password",
            pact_broker_password,
            required=True,
        )
    else:
        pact_broker_url = ""
        pact_broker_username = ""
        pact_broker_password = ""
    return pact_broker_url, pact_broker_username, pact_broker_password


def clean_media_storage(media_storage):
    """Return the media storage."""
    return (
        media_storage
        or click.prompt(
            "Media storage",
            default=MEDIA_STORAGE_DIGITALOCEAN_S3,
            type=click.Choice(MEDIA_STORAGE_CHOICES, case_sensitive=False),
        ).lower()
    )


def clean_gitlab_group_data(
    project_slug,
    gitlab_group_slug,
    gitlab_private_token,
    gitlab_group_owners,
    gitlab_group_maintainers,
    gitlab_group_developers,
    quiet=False,
):
    """Return GitLab group data."""
    if gitlab_group_slug or (
        gitlab_group_slug is None
        and click.confirm(warning("Do you want to use GitLab?"), default=True)
    ):
        gitlab_group_slug = slugify(
            gitlab_group_slug or click.prompt("GitLab group slug", default=project_slug)
        )
        quiet or click.confirm(
            warning(
                f'Make sure the GitLab "{gitlab_group_slug}" group exists '
                "before proceeding. Continue?"
            ),
            abort=True,
        )
        gitlab_private_token = gitlab_private_token or click.prompt(
            "GitLab private token (with API scope enabled)", hide_input=True
        )
        gitlab_group_owners = (
            gitlab_group_owners
            if gitlab_group_owners is not None
            else click.prompt("Comma-separated GitLab group owners", default="")
        )
        gitlab_group_maintainers = (
            gitlab_group_maintainers
            if gitlab_group_maintainers is not None
            else click.prompt("Comma-separated GitLab group maintainers", default="")
        )
        gitlab_group_developers = (
            gitlab_group_developers
            if gitlab_group_developers is not None
            else click.prompt("Comma-separated GitLab group developers", default="")
        )
    else:
        gitlab_group_slug = ""
        gitlab_private_token = ""
        gitlab_group_owners = ""
        gitlab_group_maintainers = ""
        gitlab_group_developers = ""
    return (
        gitlab_group_slug,
        gitlab_private_token,
        gitlab_group_owners,
        gitlab_group_maintainers,
        gitlab_group_developers,
    )


def clean_s3_media_storage_data(
    media_storage,
    digitalocean_token,
    s3_region,
    s3_host,
    s3_access_id,
    s3_secret_key,
    s3_bucket_name,
):
    """Return S3 media storage data."""
    if media_storage == MEDIA_STORAGE_DIGITALOCEAN_S3:
        digitalocean_token = validate_or_prompt_password(
            "DigitalOcean token",
            digitalocean_token,
            required=True,
        )
        s3_region = s3_region or click.prompt(
            "DigitalOcean Spaces region",
            default=DIGITALOCEAN_SPACES_REGION_DEFAULT,
        )
        s3_host = "digitaloceanspaces.com"
        s3_bucket_name = ""
    elif media_storage == MEDIA_STORAGE_AWS_S3:
        digitalocean_token = ""
        s3_region = s3_region or click.prompt(
            "AWS S3 region name",
            default=AWS_S3_REGION_DEFAULT,
        )
        s3_host = ""
        s3_bucket_name = s3_bucket_name or click.prompt(
            "AWS S3 bucket name",
        )
    s3_access_id = validate_or_prompt_password(
        "S3 Access Key ID",
        s3_access_id,
        required=True,
    )
    s3_secret_key = validate_or_prompt_password(
        "S3 Secret Access Key",
        s3_secret_key,
        required=True,
    )
    return (
        digitalocean_token,
        s3_region,
        s3_host,
        s3_access_id,
        s3_secret_key,
        s3_bucket_name,
    )
