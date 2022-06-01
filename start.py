#!/usr/bin/env python
"""Initialize a template based web project."""

import os
from pathlib import Path

import click

from bootstrap.collector import collect
from bootstrap.constants import (
    DEPLOYMENT_TYPE_CHOICES,
    ENVIRONMENT_DISTRIBUTION_CHOICES,
    GITLAB_TOKEN_ENV_VAR,
    MEDIA_STORAGE_CHOICES,
)
from bootstrap.exceptions import BootstrapError
from bootstrap.helpers import slugify_option
from bootstrap.runner import Runner

OUTPUT_DIR = os.getenv("OUTPUT_BASE_DIR") or "."


@click.command()
@click.option("--uid", type=int)
@click.option("--gid", type=int)
@click.option(
    "--output-dir",
    default=OUTPUT_DIR,
    type=click.Path(
        exists=True, path_type=Path, file_okay=False, readable=True, writable=True
    ),
)
@click.option("--project-name")
@click.option("--project-slug", callback=slugify_option)
@click.option("--project-dirname")
@click.option("--backend-type")
@click.option("--backend-service-slug")
@click.option("--backend-service-port", default=8000, type=int)
@click.option("--frontend-type")
@click.option("--frontend-service-slug")
@click.option("--frontend-service-port", default=3000, type=int)
@click.option(
    "--deployment-type",
    type=click.Choice(DEPLOYMENT_TYPE_CHOICES, case_sensitive=False),
)
@click.option("--terraform-backend")
@click.option("--terraform-cloud-hostname")
@click.option("--terraform-cloud-token")
@click.option("--terraform-cloud-organization")
@click.option(
    "--terraform-cloud-organization-create/--terraform-cloud-organization-create-skip",
    is_flag=True,
    default=None,
)
@click.option("--terraform-cloud-admin-email")
@click.option("--vault-token")
@click.option("--digitalocean-token")
@click.option(
    "--kubernetes-cluster-ca-certificate",
    type=click.Path(dir_okay=False, exists=True, resolve_path=True),
)
@click.option("--kubernetes-host")
@click.option("--kubernetes-token")
@click.option(
    "--environment-distribution", type=click.Choice(ENVIRONMENT_DISTRIBUTION_CHOICES)
)
@click.option("--project-domain")
@click.option("--subdomain-dev")
@click.option("--subdomain-stage")
@click.option("--subdomain-prod")
@click.option("--subdomain-monitoring")
@click.option("--project-url-dev")
@click.option("--project-url-stage")
@click.option("--project-url-prod")
@click.option("--letsencrypt-certificate-email")  # ADD TO README
@click.option(
    "--digitalocean-domain-create/--digitalocean-domain-create-skip",
    is_flag=True,
    default=None,
)  # ADD TO README
@click.option(
    "--digitalocean-dns-records-create/--digitalocean-dns-records-create-skip",
    is_flag=True,
    default=None,
)  # ADD TO README
@click.option("--digitalocean-k8s-cluster-region")
@click.option("--digitalocean-database-cluster-region")
@click.option("--digitalocean-database-cluster-node-size")
@click.option("--postgres-image")
@click.option("--postgres-persistent-volume-capacity")
@click.option("--postgres-persistent-volume-claim-capacity")
@click.option("--postgres-persistent-volume-host-path")
@click.option("--use-redis/--no-redis", is_flag=True, default=None)
@click.option("--redis-image")
@click.option("--digitalocean-redis-cluster-region")
@click.option("--digitalocean-redis-cluster-node-size")
@click.option("--sentry-org")
@click.option("--sentry-url")
@click.option("--backend-sentry-dsn")
@click.option("--frontend-sentry-dsn")
@click.option("--sentry-auth-token")
@click.option("--pact-broker-url")
@click.option("--pact-broker-username")
@click.option("--pact-broker-password")
@click.option(
    "--media-storage",
    type=click.Choice(MEDIA_STORAGE_CHOICES, case_sensitive=False),
)
@click.option("--s3-region")
@click.option("--s3-host")
@click.option("--s3-access-id")
@click.option("--s3-secret-key")
@click.option("--s3-bucket-name")
@click.option("--gitlab-private-token", envvar=GITLAB_TOKEN_ENV_VAR)
@click.option("--gitlab-group-slug")
@click.option("--gitlab-group-owners")
@click.option("--gitlab-group-maintainers")
@click.option("--gitlab-group-developers")
@click.option("--terraform-dir", type=click.Path())
@click.option("--logs-dir", type=click.Path())
@click.option("--quiet", is_flag=True)
def main(**options):
    """Run the setup."""
    try:
        Runner(**collect(**options)).run()
    except BootstrapError as e:
        raise click.Abort() from e


if __name__ == "__main__":
    main()
