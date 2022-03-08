"""Collect options to initialize a template based web project."""

import shutil
from functools import partial
from pathlib import Path

import click
import validators
from slugify import slugify

from bootstrap.constants import (
    BACKEND_TYPE_CHOICES,
    DEPLOYMENT_TYPE_CHOICES,
    DEPLOYMENT_TYPE_DEFAULT,
    DIGITALOCEAN_SPACES_REGION_DEFAULT,
    ENVIRONMENT_DISTRIBUTION_CHOICES,
    ENVIRONMENT_DISTRIBUTION_DEFAULT,
    ENVIRONMENT_DISTRIBUTION_PROMPT,
    FRONTEND_TYPE_CHOICES,
    MEDIA_STORAGE_CHOICES,
    MEDIA_STORAGE_DEFAULT,
)

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
    environment_distribution,
    project_domain,
    domain_prefix_dev,
    domain_prefix_stage,
    domain_prefix_prod,
    project_url_dev,
    project_url_stage,
    project_url_prod,
    digitalocean_k8s_cluster_region,
    digitalocean_database_cluster_region,
    digitalocean_database_cluster_node_size,
    sentry_org,
    sentry_url,
    sentry_auth_token,
    use_pact,
    pact_broker_url,
    pact_broker_username,
    pact_broker_password,
    media_storage,
    digitalocean_spaces_bucket_region,
    digitalocean_spaces_access_id,
    digitalocean_spaces_secret_key,
    use_gitlab,
    gitlab_private_token,
    gitlab_group_slug,
    gitlab_group_owners,
    gitlab_group_maintainers,
    gitlab_group_developers,
    terraform_dir,
    logs_dir,
):
    """Collect options and run the bootstrap."""
    project_slug = clean_project_slug(project_name, project_slug)
    project_dirname = slugify(project_slug, separator="")
    service_dir = clean_service_dir(output_dir, project_dirname)
    if backend_type := clean_backend_type(backend_type):
        backend_service_slug = clean_backend_service_slug(backend_service_slug)
    if frontend_type := clean_frontend_type(frontend_service_slug):
        frontend_service_slug = clean_frontend_service_slug(frontend_service_slug)
    environment_distribution = clean_environment_distribution(environment_distribution)
    deployment_type = clean_deployment_type(deployment_type)
    if digitalocean_enabled := ("digitalocean" in deployment_type):
        digitalocean_token = validate_or_prompt_password(
            digitalocean_token, "DigitalOcean token", required=True
        )
        project_domain = clean_project_domain(project_domain)
    else:
        project_domain = None
    (
        domain_prefix_dev,
        domain_prefix_stage,
        domain_prefix_prod,
        project_url_dev,
        project_url_stage,
        project_url_prod,
    ) = clean_project_urls(
        project_slug,
        project_domain,
        domain_prefix_dev,
        domain_prefix_stage,
        domain_prefix_prod,
        project_url_dev,
        project_url_stage,
        project_url_prod,
    )
    if digitalocean_enabled:
        (
            digitalocean_k8s_cluster_region,
            digitalocean_database_cluster_region,
            digitalocean_database_cluster_node_size,
        ) = clean_digitalocean_clusters_data(
            digitalocean_k8s_cluster_region,
            digitalocean_database_cluster_region,
            digitalocean_database_cluster_node_size,
        )
    if sentry_org := clean_sentry_org(sentry_org):
        sentry_url = validate_or_prompt_url(
            sentry_url, "Sentry URL", default="https://sentry.io/", required=True
        )
        sentry_auth_token = validate_or_prompt_password(
            sentry_auth_token, "Sentry auth token", required=True
        )
    if use_pact := clean_use_pact(use_pact):
        (
            pact_broker_url,
            pact_broker_username,
            pact_broker_password,
        ) = clean_pact_broker_data(
            pact_broker_url, pact_broker_username, pact_broker_password
        )
    media_storage = clean_media_storage(media_storage)
    if use_gitlab := clean_use_gitlab(use_gitlab):
        (
            gitlab_group_slug,
            gitlab_private_token,
            gitlab_group_owners,
            gitlab_group_maintainers,
            gitlab_group_developers,
        ) = clean_gitlab_group_data(
            media_storage,
            gitlab_group_slug,
            gitlab_private_token,
            gitlab_group_owners,
            gitlab_group_maintainers,
            gitlab_group_developers,
        )
        if media_storage == "s3-digitalocean":
            (
                digitalocean_token,
                digitalocean_spaces_bucket_region,
                digitalocean_spaces_access_id,
                digitalocean_spaces_secret_key,
            ) = clean_digitalocean_media_storage_data()
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
        "environment_distribution": environment_distribution,
        "project_domain": project_domain,
        "domain_prefix_dev": domain_prefix_dev,
        "domain_prefix_stage": domain_prefix_stage,
        "domain_prefix_prod": domain_prefix_prod,
        "project_url_dev": project_url_dev,
        "project_url_stage": project_url_stage,
        "project_url_prod": project_url_prod,
        "digitalocean_k8s_cluster_region": digitalocean_k8s_cluster_region,
        "digitalocean_database_cluster_region": digitalocean_database_cluster_region,
        "digitalocean_database_cluster_node_size": (
            digitalocean_database_cluster_node_size
        ),
        "sentry_org": sentry_org,
        "sentry_url": sentry_url,
        "sentry_auth_token": sentry_auth_token,
        "use_pact": use_pact,
        "pact_broker_url": pact_broker_url,
        "pact_broker_username": pact_broker_username,
        "pact_broker_password": pact_broker_password,
        "media_storage": media_storage,
        "digitalocean_spaces_bucket_region": digitalocean_spaces_bucket_region,
        "digitalocean_spaces_access_id": digitalocean_spaces_access_id,
        "digitalocean_spaces_secret_key": digitalocean_spaces_secret_key,
        "use_gitlab": use_gitlab,
        "gitlab_private_token": gitlab_private_token,
        "gitlab_group_slug": gitlab_group_slug,
        "gitlab_group_owners": gitlab_group_owners,
        "gitlab_group_maintainers": gitlab_group_maintainers,
        "gitlab_group_developers": gitlab_group_developers,
        "terraform_dir": terraform_dir,
        "logs_dir": logs_dir,
    }


def validate_or_prompt_url(value, message, default=None, required=False):
    """Validate the given URL or prompt until a valid value is provided."""
    if value is not None:
        if not required and value == "" or validators.url(value):
            return value.strip("/")
        else:
            click.echo("Please type a valid URL!")
    new_value = click.prompt(message, default=default)
    return validate_or_prompt_url(new_value, message, default, required)


def validate_or_prompt_password(value, message, default=None, required=False):
    """Validate the given password or prompt until a valid value is provided."""
    if value is not None:
        if not required and value == "" or validators.length(value, min=8):
            return value
        else:
            click.echo("Please type at least 8 chars!")
    new_value = click.prompt(message, default=default, hide_input=True)
    return validate_or_prompt_password(new_value, message, default, required)


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
            default=BACKEND_TYPE_CHOICES[0],
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
        frontend_type in FRONTEND_TYPE_CHOICES
        and frontend_type
        or click.prompt(
            "Frontend type",
            default=FRONTEND_TYPE_CHOICES[0],
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
        deployment_type in DEPLOYMENT_TYPE_CHOICES
        and deployment_type
        or click.prompt(
            "Deploy type",
            default=DEPLOYMENT_TYPE_DEFAULT,
            type=click.Choice(DEPLOYMENT_TYPE_CHOICES, case_sensitive=False),
        )
    ).lower()


def clean_environment_distribution(environment_distribution):
    """Return the environment distribution."""
    return (
        environment_distribution in ENVIRONMENT_DISTRIBUTION_CHOICES
        and environment_distribution
        or click.prompt(
            ENVIRONMENT_DISTRIBUTION_PROMPT,
            default=ENVIRONMENT_DISTRIBUTION_DEFAULT,
            type=click.Choice(ENVIRONMENT_DISTRIBUTION_CHOICES),
        )
    )


def clean_project_domain(project_domain):
    """Return the project domain."""
    return project_domain or click.prompt(
        "Project domain (e.g. 20tab.com, "
        "if you prefer to skip DigitalOcean DNS configuration, leave blank)",
        default="",
    )


def clean_project_urls(
    project_slug,
    project_domain,
    domain_prefix_dev,
    domain_prefix_stage,
    domain_prefix_prod,
    project_url_dev,
    project_url_stage,
    project_url_prod,
):
    """Return project URLs."""
    if project_domain:
        domain_prefix_dev = domain_prefix_dev or click.prompt(
            "Development domain prefix", default="dev"
        )
        domain_prefix_stage = domain_prefix_stage or click.prompt(
            "Staging domain prefix", default="stage"
        )
        domain_prefix_prod = domain_prefix_prod or click.prompt(
            "Production domain prefix", default="www"
        )
        project_url_dev = f"https://{domain_prefix_dev}.{project_domain}"
        project_url_stage = f"https://{domain_prefix_stage}.{project_domain}"
        project_url_prod = f"https://{domain_prefix_prod}.{project_domain}"
    else:
        domain_prefix_dev = domain_prefix_stage = domain_prefix_prod = ""
        project_url_dev = validate_or_prompt_url(
            project_url_dev or None,
            "Development environment complete URL",
            default=f"https://dev.{project_slug}.com",
        )
        project_url_stage = validate_or_prompt_url(
            project_url_stage or None,
            "Staging environment complete URL",
            default=f"https://stage.{project_slug}.com",
        )
        project_url_prod = validate_or_prompt_url(
            project_url_prod or None,
            "Production environment complete URL",
            default=f"https://www.{project_slug}.com",
        )
    return (
        domain_prefix_dev,
        domain_prefix_stage,
        domain_prefix_prod,
        project_url_dev,
        project_url_stage,
        project_url_prod,
    )


def clean_sentry_org(sentry_org):
    """Return the Sentry organization."""
    return sentry_org or click.prompt(
        'Sentry organization (e.g. "20tab", leave blank if unused)',
        default="",
    )


def clean_digitalocean_clusters_data(
    digitalocean_k8s_cluster_region,
    digitalocean_database_cluster_region,
    digitalocean_database_cluster_node_size,
):
    """Return DigitalOcean k8s and database clusters data."""
    # TODO: ask these settings for each stack
    digitalocean_k8s_cluster_region = digitalocean_k8s_cluster_region or click.prompt(
        "Kubernetes cluster Digital Ocean region", default="fra1"
    )
    digitalocean_database_cluster_region = (
        digitalocean_database_cluster_region
        or click.prompt("Database cluster Digital Ocean region", default="fra1")
    )
    digitalocean_database_cluster_node_size = (
        digitalocean_database_cluster_node_size
        or click.prompt("Database cluster node size", default="db-s-1vcpu-2gb")
    )
    return (
        digitalocean_k8s_cluster_region,
        digitalocean_database_cluster_region,
        digitalocean_database_cluster_node_size,
    )


def clean_use_pact(use_pact):
    """Tell whether Pact should be configured."""
    if use_pact is None:
        return click.confirm(warning("Do you want to configure Pact?"), default=True)
    return use_pact


def clean_pact_broker_data(pact_broker_url, pact_broker_username, pact_broker_password):
    """Return Pact broker data."""
    pact_broker_url = validate_or_prompt_url(
        pact_broker_url,
        "Pact broker URL (e.g. https://broker.20tab.com/)",
        required=True,
    )
    pact_broker_username = pact_broker_username or click.prompt(
        "Pact broker username",
    )
    pact_broker_password = validate_or_prompt_password(
        pact_broker_password,
        "Pact broker password",
        required=True,
    )
    return pact_broker_url, pact_broker_username, pact_broker_password


def clean_media_storage(media_storage):
    """Return the media storage."""
    return (
        media_storage
        or click.prompt(
            "Media storage",
            default=MEDIA_STORAGE_DEFAULT,
            type=click.Choice(MEDIA_STORAGE_CHOICES, case_sensitive=False),
        ).lower()
    )


def clean_use_gitlab(use_gitlab):
    """Tell whether Gitlab should be used."""
    if use_gitlab is None:
        return click.confirm(warning("Do you want to configure Gitlab?"), default=True)
    return use_gitlab


def clean_gitlab_group_data(
    project_slug,
    gitlab_group_slug,
    gitlab_private_token,
    gitlab_group_owners,
    gitlab_group_maintainers,
    gitlab_group_developers,
):
    """Return Gitlab group data."""
    gitlab_group_slug = slugify(
        gitlab_group_slug or click.prompt("Gitlab group slug", default=project_slug)
    )
    click.confirm(
        warning(
            f'Make sure the Gitlab "{gitlab_group_slug}" group exists '
            "before proceeding. Continue?"
        ),
        abort=True,
    )
    gitlab_private_token = gitlab_private_token or click.prompt(
        "Gitlab private token (with API scope enabled)", hide_input=True
    )
    gitlab_group_owners = gitlab_group_owners or click.prompt(
        "Comma-separated Gitlab group owners", default=""
    )
    gitlab_group_maintainers = gitlab_group_maintainers or click.prompt(
        "Comma-separated Gitlab group maintainers", default=""
    )
    gitlab_group_developers = gitlab_group_developers or click.prompt(
        "Comma-separated Gitlab group developers", default=""
    )
    return (
        gitlab_group_slug,
        gitlab_private_token,
        gitlab_group_owners,
        gitlab_group_maintainers,
        gitlab_group_developers,
    )


def clean_digitalocean_media_storage_data(
    digitalocean_token,
    digitalocean_spaces_bucket_region,
    digitalocean_spaces_access_id,
    digitalocean_spaces_secret_key,
):
    """Return DigitalOcean media storage data."""
    digitalocean_token = validate_or_prompt_password(
        digitalocean_token,
        "DigitalOcean token",
        required=True,
    )
    digitalocean_spaces_bucket_region = (
        digitalocean_spaces_bucket_region
        or click.prompt(
            "DigitalOcean Spaces region",
            default=DIGITALOCEAN_SPACES_REGION_DEFAULT,
        )
    )
    digitalocean_spaces_access_id = validate_or_prompt_password(
        digitalocean_spaces_access_id,
        "DigitalOcean Spaces Access Key ID",
        required=True,
    )
    digitalocean_spaces_secret_key = validate_or_prompt_password(
        digitalocean_spaces_secret_key,
        "DigitalOcean Spaces Secret Access Key",
        required=True,
    )
    return (
        digitalocean_token,
        digitalocean_spaces_bucket_region,
        digitalocean_spaces_access_id,
        digitalocean_spaces_secret_key,
    )
