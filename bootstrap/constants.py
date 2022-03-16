"""Web project initialization CLI constants."""

EMPTY_SERVICE_TYPE = "none"

BACKEND_TEMPLATE_URLS = {
    "django": "https://github.com/20tab/django-continuous-delivery"
}

BACKEND_TYPE_CHOICES = ["django", EMPTY_SERVICE_TYPE]

BACKEND_TYPE_DEFAULT = "django"

DEFAULT_DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE = "db-s-1vcpu-2gb"

DEFAULT_DIGITALOCEAN_REDIS_CLUSTER_NODE_SIZE = "db-s-1vcpu-2gb"

DEFAULT_SERVICE_SLUG = "orchestrator"

DEPLOYMENT_TYPE_CHOICES = ["k8s-digitalocean", "k8s-other"]

DEPLOYMENT_TYPE_DEFAULT = "k8s-digitalocean"

ENVIRONMENT_DISTRIBUTION_CHOICES = ["1", "2", "3"]

ENVIRONMENT_DISTRIBUTION_PROMPT = """Choose the environments distribution:
  1 - All environments share the same stack (Default)
  2 - Dev and Stage environments share the same stack, Prod has its own
  3 - Each environment has its own stack
"""

ENVIRONMENT_DISTRIBUTION_DEFAULT = "1"

DIGITALOCEAN_SPACES_REGION_DEFAULT = "fra1"

FRONTEND_TEMPLATE_URLS = {
    "nextjs": "https://github.com/20tab/react-ts-continuous-delivery"
}

FRONTEND_TYPE_CHOICES = ["nextjs", EMPTY_SERVICE_TYPE]

FRONTEND_TYPE_DEFAULT = "nextjs"

GITLAB_TOKEN_ENV_VAR = "GITLAB_PRIVATE_TOKEN"

MEDIA_STORAGE_CHOICES = ["local", "s3-digitalocean", "none"]

MEDIA_STORAGE_DEFAULT = "s3-digitalocean"

SUBREPOS_DIR = ".subrepos"
