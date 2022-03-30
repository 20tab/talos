locals {
  project_slug = "{{ cookiecutter.project_slug }}"

  stack_resources_prefix = var.stack_slug == "main" ? local.project_slug : "${local.project_slug}-${var.stack_slug}"
  env_resources_prefix   = "${local.project_slug}-${var.env_slug}"

  namespace = kubernetes_namespace_v1.main.metadata[0].name

  project_host = regexall("https?://([^/]+)", var.project_url)[0][0]

  registry_username = coalesce(var.registry_username, "${local.project_slug}-k8s-regcred")

  use_s3 = length(regexall("s3", var.media_storage)) > 0

  postgres_dump_enabled = var.env_slug == "prod" && local.use_s3 && length(
    compact(
      [
        var.s3_bucket_access_id,
        var.s3_bucket_secret_key,
        var.s3_bucket_name,
        var.s3_host
      ]
    )
  ) == 4

terraform {
  backend "http" {
  }

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.9.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

/* Providers */

provider "kubernetes" {
  host                   = var.kubernetes_host
  token                  = var.kubernetes_token
  cluster_ca_certificate = base64decode(var.kubernetes_cluster_ca_certificate)
}

/* Namespace */

resource "kubernetes_namespace_v1" "main" {
  metadata {
    name = local.env_resources_prefix
  }
}

/* Databases */

module "postgres" {
  source = "../modules/kubernetes/postgres"

  namespace = local.namespace

  resources_prefix = local.env_resources_prefix

  postgres_image = var.postgres_image

  database_name = "${local.env_resources_prefix}-database"
  database_user = "${local.env_resources_prefix}-database-user"

  persistent_volume_capacity       = var.postgres_persistent_volume_capacity
  persistent_volume_claim_capacity = var.postgres_persistent_volume_claim_capacity
  persistent_volume_host_path      = var.postgres_persistent_volume_host_path
}

module "redis" {
  count = var.use_redis == "true" ? 1 : 0

  source = "../modules/kubernetes/redis"

  namespace = local.namespace

  resources_prefix = local.env_resources_prefix

  redis_image = var.redis_image
}

/* Routing */

module "routing" {
  source = "../modules/kubernetes/routing"

  namespace = local.namespace

  resources_prefix = local.env_resources_prefix

  project_host = local.project_host

  basic_auth_enabled  = var.basic_auth_enabled
  basic_auth_username = var.basic_auth_username
  basic_auth_password = var.basic_auth_password

  backend_middlewares  = var.backend_middlewares
  backend_service_port = var.backend_service_port
  backend_service_slug = var.backend_service_slug

  frontend_middlewares  = var.frontend_middlewares
  frontend_service_port = var.frontend_service_port
  frontend_service_slug = var.frontend_service_slug

  media_storage = var.media_storage
}

/* Secrets */

resource "kubernetes_secret_v1" "regcred" {
  metadata {
    name      = "regcred"
    namespace = local.namespace
  }
  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "${var.registry_server}" = {
          auth = "${base64encode("${local.registry_username}:${var.registry_password}")}"
        }
      }
    })
  }
  type = "kubernetes.io/dockerconfigjson"
}

/* Cron Jobs */

module "database_dump_cronjob" {
  count = local.postgres_dump_enabled ? 1 : 0

  source = "../modules/kubernetes/database-dump-cronjob"

  namespace = local.namespace

  resources_prefix = local.project_slug

  s3_host              = var.s3_host
  s3_bucket_name       = var.s3_bucket_name
  s3_bucket_access_id  = var.s3_bucket_access_id
  s3_bucket_secret_key = var.s3_bucket_secret_key
}
