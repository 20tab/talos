#!/usr/bin/env python
"""Web project initialization cli options."""

import os
import shutil
from functools import partial
from pathlib import Path

import click
from slugify import slugify

from bootstrap.constants import (
    BACKEND_TYPE_CHOICES,
    DEFAULT_SERVICE_SLUG,
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
from bootstrap.helpers import validate_or_prompt_password, validate_or_prompt_url

warning = partial(click.style, fg="yellow")


def get_output_dir(output_dir=None):
    """Return the output dir."""
    return os.getenv("OUTPUT_DIR") or output_dir


def get_project_slug(project_name, project_slug=None):
    """Return the project slug."""
    return slugify(project_slug or click.prompt("Project slug", default=project_name))


def get_project_dirname(project_slug):
    """Return the project directory name."""
    return slugify(project_slug, separator="")


def get_service_slug():
    """Return the service slug."""
    return DEFAULT_SERVICE_SLUG


def get_service_dir(output_dir, project_dirname):
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


def get_backend_type(backend_type=None):
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


def get_backend_service_slug(backend_service_slug=None, backend_type=None):
    """Return the back end service slug."""
    return backend_type and slugify(
        backend_service_slug or click.prompt("Backend service slug", default="backend"),
        separator="",
    )


def get_frontend_type(frontend_type=None):
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


def get_frontend_service_slug(frontend_service_slug=None, frontend_type=None):
    """Return the front end service slug."""
    return frontend_type and slugify(
        frontend_service_slug
        or click.prompt("Frontend service slug", default="frontend"),
        separator="",
    )


def get_deployment_type(deployment_type=None):
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


def get_is_digitalocean_enabled(deployment_type):
    """Tell whether DigitalOcean should be enabled."""
    return "digitalocean" in deployment_type


def get_digitalocean_token(digitalocean_token):
    """Return DigitalOcean token."""
    return validate_or_prompt_password(
        digitalocean_token,
        "DigitalOcean token",
        required=True,
    )


def get_environment_distribution(environment_distribution=None):
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


def get_project_domain(project_domain):
    """Return the project domain."""
    return (
        project_domain
        or click.prompt(
            "Project domain (e.g. 20tab.com, "
            "if you prefer to skip DigitalOcean DNS configuration, leave blank)",
            default="",
        )
    ) or None


def get_project_urls(
    project_slug,
    project_domain=None,
    domain_prefix_dev=None,
    domain_prefix_stage=None,
    domain_prefix_prod=None,
    project_url_dev=None,
    project_url_stage=None,
    project_url_prod=None,
):
    """Return project URLs."""
    if project_domain:
        domain_prefix_dev = domain_prefix_dev or click.prompt(
            "Development domain prefix",
            default="dev",
        )
        domain_prefix_stage = domain_prefix_stage or click.prompt(
            "Staging domain prefix",
            default="stage",
        )
        domain_prefix_prod = domain_prefix_prod or click.prompt(
            "Production domain prefix",
            default="www",
        )
        project_url_dev = f"https://{domain_prefix_dev}.{project_domain}"
        project_url_stage = f"https://{domain_prefix_stage}.{project_domain}"
        project_url_prod = f"https://{domain_prefix_prod}.{project_domain}"
    else:
        project_domain = ""
        domain_prefix_dev = domain_prefix_stage = domain_prefix_prod = ""
        project_url_dev = validate_or_prompt_url(
            project_url_dev,
            "Development environment complete URL",
            default=f"https://dev.{project_slug}.com",
        )
        project_url_stage = validate_or_prompt_url(
            project_url_stage,
            "Staging environment complete URL",
            default=f"https://stage.{project_slug}.com",
        )
        project_url_prod = validate_or_prompt_url(
            project_url_prod,
            "Production environment complete URL",
            default=f"https://www.{project_slug}.com",
        )
    return project_domain, project_url_dev, project_url_stage, project_url_prod


def get_sentry_org(sentry_org=None):
    """Return the Sentry organization."""
    return sentry_org or click.prompt(
        'Sentry organization (e.g. "20tab", leave blank if unused)',
        default="",
    )


def get_cluster_data(
    digitalocean_k8s_cluster_region=None,
    digitalocean_database_cluster_region=None,
    digitalocean_database_cluster_node_size=None,
):
    """Return DigitalOcean k8s regions."""
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


def get_sentry_url(sentry_url):
    """Return the Sentry URL."""
    return validate_or_prompt_url(
        sentry_url,
        "Sentry URL",
        default="https://sentry.io/",
        required=True,
    )


def get_sentry_token(sentry_auth_token):
    """Return the Sentry token."""
    return validate_or_prompt_password(
        sentry_auth_token,
        "Sentry auth token",
        required=True,
    )


def get_use_pact(use_pact=None):
    """Tell whether Pact should be configured."""
    return click.confirm(warning("Do you want to configure Pact?"), default=True)


def get_broker_data(
    pact_broker_url=None,
    pact_broker_username=None,
    pact_broker_password=None,
):
    """Return broker data."""
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


def get_media_storage():
    """Return the media storage."""
    return click.prompt(
        "Media storage",
        default=MEDIA_STORAGE_DEFAULT,
        type=click.Choice(MEDIA_STORAGE_CHOICES, case_sensitive=False),
    ).lower()


def get_use_gitlab():
    """Tell whether Gitlab should be used."""
    return click.confirm(warning("Do you want to configure Gitlab?"), default=True)


def get_gitlab_group_data(
    project_slug=None,
    gitlab_group_slug=None,
    gitlab_private_token=None,
    gitlab_group_owners=None,
    gitlab_group_maintainers=None,
    gitlab_group_developers=None,
):
    """Return Gitlab data."""
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


def get_digitalocean_media_storage_data(
    digitalocean_token=None,
    digitalocean_spaces_bucket_region=None,
    digitalocean_spaces_access_id=None,
    digitalocean_spaces_secret_key=None,
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
