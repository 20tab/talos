"""Web project initialization CLI constants."""

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DUMPS_DIR = BASE_DIR / ".dumps"

# Stacks

# BEWARE: stack names must be suitable for inclusion in Vault paths

DEV_STACK_NAME = "development"

DEV_STACK_SLUG = "dev"

STAGE_STACK_NAME = "staging"

STAGE_STACK_SLUG = "stage"

MAIN_STACK_NAME = "main"

MAIN_STACK_SLUG = "main"

STACKS_CHOICES = {
    "1": [{"name": MAIN_STACK_NAME, "slug": MAIN_STACK_SLUG}],
    "2": [
        {"name": DEV_STACK_NAME, "slug": DEV_STACK_SLUG},
        {"name": MAIN_STACK_NAME, "slug": MAIN_STACK_SLUG},
    ],
    "3": [
        {"name": DEV_STACK_NAME, "slug": DEV_STACK_SLUG},
        {"name": STAGE_STACK_NAME, "slug": STAGE_STACK_SLUG},
        {"name": MAIN_STACK_NAME, "slug": MAIN_STACK_SLUG},
    ],
}

# Environments

# BEWARE: environment names must be suitable for inclusion in Vault paths

DEV_ENV_NAME = "development"

DEV_ENV_SLUG = "dev"

DEV_ENV_STACK_CHOICES: dict[str, str] = {
    "1": MAIN_STACK_SLUG,
}

STAGE_ENV_NAME = "staging"

STAGE_ENV_SLUG = "stage"

STAGE_ENV_STACK_CHOICES: dict[str, str] = {
    "1": MAIN_STACK_SLUG,
    "2": DEV_STACK_SLUG,
}

PROD_ENV_NAME = "production"

PROD_ENV_SLUG = "prod"

PROD_ENV_STACK_CHOICES: dict[str, str] = {}

# Env vars

GITLAB_TOKEN_ENV_VAR = "GITLAB_PRIVATE_TOKEN"

VAULT_TOKEN_ENV_VAR = "VAULT_TOKEN"

# Subrepos

BACKEND_TEMPLATE_URLS = {
    "django": "https://github.com/20tab/django-continuous-delivery"
}

FRONTEND_TEMPLATE_URLS = {
    "nextjs": "https://github.com/20tab/nextjs-continuous-delivery",
    "nextjs-light": "https://github.com/20tab/react-continuous-delivery",
}

SUBREPOS_DIR = Path(__file__).parent.parent / ".subrepos"

# Services type

SERVICE_SLUG_DEFAULT = "orchestrator"

EMPTY_SERVICE_TYPE = "none"

BACKEND_TYPE_DEFAULT = "django"

BACKEND_TYPE_CHOICES = [BACKEND_TYPE_DEFAULT, EMPTY_SERVICE_TYPE]

FRONTEND_TYPE_DEFAULT = "nextjs"

FRONTEND_TYPE_LIGHT = "nextjs-light"

FRONTEND_TYPE_CHOICES = [FRONTEND_TYPE_DEFAULT, FRONTEND_TYPE_LIGHT, EMPTY_SERVICE_TYPE]

# Deployment type

DEPLOYMENT_TYPE_DIGITALOCEAN = "digitalocean-k8s"

DEPLOYMENT_TYPE_OTHER = "other-k8s"

DEPLOYMENT_TYPE_CHOICES = [DEPLOYMENT_TYPE_DIGITALOCEAN, DEPLOYMENT_TYPE_OTHER]

# Environments distribution

ENVIRONMENTS_DISTRIBUTION_DEFAULT = "1"

ENVIRONMENTS_DISTRIBUTION_CHOICES = [ENVIRONMENTS_DISTRIBUTION_DEFAULT, "2", "3"]

ENVIRONMENTS_DISTRIBUTION_PROMPT = """Choose the environments distribution:
  1 - All environments share the same stack (Default)
  2 - Dev and Stage environments share the same stack, Prod has its own
  3 - Each environment has its own stack
"""

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

# Dump

DUMP_EXCLUDED_OPTIONS = (
    "backend_sentry_dsn",
    "digitalocean_token",
    "frontend_sentry_dsn",
    "gitlab_token",
    "kubernetes_token",
    "pact_broker_password",
    "s3_access_id",
    "s3_secret_key",
    "sentry_auth_token",
    "service_dir",
    "terraform_cloud_token",
    "vault_token",
)
