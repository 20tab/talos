"""Web project initialization CLI constants."""

# Env vars

GITLAB_TOKEN_ENV_VAR = "GITLAB_PRIVATE_TOKEN"

# Subrepos

BACKEND_TEMPLATE_URLS = {
    "django": "https://github.com/20tab/django-continuous-delivery"
}

FRONTEND_TEMPLATE_URLS = {
    "nextjs": "https://github.com/20tab/react-ts-continuous-delivery"
}

SUBREPOS_DIR = ".subrepos"

# Services type

ORCHESTRATOR_SERVICE_SLUG = "orchestrator"

EMPTY_SERVICE_TYPE = "none"

BACKEND_TYPE_DEFAULT = "django"

BACKEND_TYPE_CHOICES = [BACKEND_TYPE_DEFAULT, EMPTY_SERVICE_TYPE]

FRONTEND_TYPE_DEFAULT = "nextjs"

FRONTEND_TYPE_CHOICES = [FRONTEND_TYPE_DEFAULT, EMPTY_SERVICE_TYPE]

# Deployment type

DEPLOYMENT_TYPE_DEFAULT = "digitalocean-k8s"

DEPLOYMENT_TYPE_OTHER = "other-k8s"

DEPLOYMENT_TYPE_CHOICES = [DEPLOYMENT_TYPE_DEFAULT, DEPLOYMENT_TYPE_OTHER]

# Environments distribution

ENVIRONMENT_DISTRIBUTION_DEFAULT = "1"

ENVIRONMENT_DISTRIBUTION_CHOICES = [ENVIRONMENT_DISTRIBUTION_DEFAULT, "2", "3"]

ENVIRONMENT_DISTRIBUTION_PROMPT = """Choose the environments distribution:
  1 - All environments share the same stack (Default)
  2 - Dev and Stage environments share the same stack, Prod has its own
  3 - Each environment has its own stack
"""

# DigitalOcean services

DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE_DEFAULT = "db-s-1vcpu-2gb"

DIGITALOCEAN_REDIS_CLUSTER_NODE_SIZE_DEFAULT = "db-s-1vcpu-2gb"

DIGITALOCEAN_SPACES_REGION_DEFAULT = "fra1"

# Media storage

MEDIA_STORAGE_DEFAULT = "s3-digitalocean"

MEDIA_STORAGE_CHOICES = [MEDIA_STORAGE_DEFAULT, "local", "none"]
