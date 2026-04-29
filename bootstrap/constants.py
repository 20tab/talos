"""Web project initialization CLI constants."""

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DUMPS_DIR = BASE_DIR / ".dumps"

# Environments

# BEWARE: environment names must be suitable for inclusion in Vault paths

DEV_ENV_NAME = "development"

DEV_ENV_SLUG = "dev"

STAGE_ENV_NAME = "staging"

STAGE_ENV_SLUG = "stage"

PROD_ENV_NAME = "production"

PROD_ENV_SLUG = "prod"

ENV_NAMES = [DEV_ENV_NAME, STAGE_ENV_NAME, PROD_ENV_NAME]

# Env vars

GITLAB_TOKEN_ENV_VAR = "GITLAB_PRIVATE_TOKEN"

VAULT_TOKEN_ENV_VAR = "VAULT_TOKEN"

# Subrepos

BACKEND_TEMPLATE_URLS = {
    "django": "https://github.com/20tab/django-continuous-delivery"
}

FRONTEND_TEMPLATE_URLS = {
    "nextjs": "https://github.com/20tab/nextjs-continuous-delivery",
    "nextjs-light": "https://github.com/20tab/nextjs-light-continuous-delivery",
}

SUBREPOS_DIR = Path(__file__).parent.parent / ".subrepos"

# Services type

SERVICE_SLUG_DEFAULT = "platform"

EMPTY_SERVICE_TYPE = "none"

BACKEND_TYPE_DEFAULT = "django"

BACKEND_TYPE_CHOICES = [BACKEND_TYPE_DEFAULT, EMPTY_SERVICE_TYPE]

FRONTEND_TYPE_DEFAULT = "nextjs"

FRONTEND_TYPE_LIGHT = "nextjs-light"

FRONTEND_TYPE_CHOICES = [FRONTEND_TYPE_DEFAULT, FRONTEND_TYPE_LIGHT, EMPTY_SERVICE_TYPE]

# DigitalOcean services

DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE_DEFAULT = "db-s-1vcpu-2gb"

DIGITALOCEAN_REDIS_CLUSTER_NODE_SIZE_DEFAULT = "db-s-1vcpu-2gb"

DIGITALOCEAN_SPACES_REGION_DEFAULT = "fra1"

# AWS services

AWS_S3_REGION_DEFAULT = "eu-central-1"

# Media storage

MEDIA_STORAGE_DIGITALOCEAN_S3 = "digitalocean-s3"

MEDIA_STORAGE_AWS_S3 = "aws-s3"

MEDIA_STORAGE_CHOICES = [
    MEDIA_STORAGE_DIGITALOCEAN_S3,
    MEDIA_STORAGE_AWS_S3,
    "local",
    "none",
]

# Terraform backend

TERRAFORM_BACKEND_GITLAB = "gitlab"

TERRAFORM_BACKEND_TFC = "terraform-cloud"

TERRAFORM_BACKEND_CHOICES = [TERRAFORM_BACKEND_TFC, TERRAFORM_BACKEND_GITLAB]

# GitLab

GITLAB_URL_DEFAULT = "https://gitlab.com"

# Clusters

CLUSTER_DEV_SLUG = "dev"

CLUSTER_MAIN_SLUG = "main"

CLUSTERS_DEFAULT = [CLUSTER_DEV_SLUG, CLUSTER_MAIN_SLUG]

# Core providers (per cluster, multi-select)

CORE_PROVIDER_AWS = "aws"

CORE_PROVIDER_DIGITALOCEAN = "digitalocean"

CORE_PROVIDER_CHOICES = [CORE_PROVIDER_AWS, CORE_PROVIDER_DIGITALOCEAN]

# Environment-to-cluster mapping

ENV_TO_CLUSTER_DEFAULT: dict[str, str] = {
    DEV_ENV_NAME: CLUSTER_DEV_SLUG,
    STAGE_ENV_NAME: CLUSTER_DEV_SLUG,
    PROD_ENV_NAME: CLUSTER_MAIN_SLUG,
}

# Vault — auth roles are shared 20tab-wide on the gitlab-jwt backend

VAULT_PLATFORM_ROLE = "platform-gitlab-job"

VAULT_SERVICE_ROLE = "service-gitlab-job"

# Minos

MINOS_PLATFORM_IMAGE = "registry.gitlab.com/20tab-open/minos/platform:latest"

MINOS_SERVICE_IMAGE = "registry.gitlab.com/20tab-open/minos/service:latest"

# OpenTofu

OPENTOFU_COMPONENT_VERSION = "3.11.0"

OPENTOFU_VERSION = "1.10.6"

# Python

PYTHON_VERSION_DEFAULT = "3.14"

# Node

NODE_VERSION_DEFAULT = "24.14.0"

# Dump

DUMP_EXCLUDED_OPTIONS = (
    "backend_sentry_dsn",
    "digitalocean_token",
    "frontend_sentry_dsn",
    "gitlab_token",
    "pact_broker_password",
    "s3_access_id",
    "s3_secret_key",
    "sentry_auth_token",
    "service_dir",
    "terraform_cloud_token",
    "vault_token",
)
