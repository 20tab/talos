locals {
  project_slug = "{{ cookiecutter.project_slug }}"

  media_storage = "{{ cookiecutter.media_storage }}"

  core_resource_name_prefix = var.stack_slug == "main" ? local.project_slug : "${local.project_slug}-${var.stack_slug}"

  namespace = kubernetes_namespace_v1.main.metadata[0].name

  project_host = regexall("https?://([^/]+)", var.project_url)[0][0]

  registry_username = coalesce(var.registry_username, "${local.project_slug}-k8s-regcred")

  use_s3 = length(regexall("s3", local.media_storage)) > 0

  s3_host        = local.media_storage == "digitalocean-s3" ? "digitaloceanspaces.com" : var.s3_host
  s3_bucket_name = local.media_storage == "digitalocean-s3" ? "${local.core_resource_name_prefix}-s3-bucket" : var.s3_bucket_name

  postgres_dump_enabled = alltrue(
    [
      var.env_slug == "prod",
      local.use_s3,
      var.s3_region != "",
      var.s3_access_id != "",
      var.s3_secret_key != "",
      local.s3_host != "",
      local.s3_bucket_name != "",
    ]
  )
}

terraform {
  backend "http" {
  }

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.9.0"
    }
  }
}

/* Providers */

provider "digitalocean" {
  token = var.digitalocean_token

  spaces_access_id  = var.s3_access_id
  spaces_secret_key = var.s3_secret_key
}

provider "kubernetes" {
  host  = data.digitalocean_kubernetes_cluster.main.endpoint
  token = data.digitalocean_kubernetes_cluster.main.kube_config[0].token
  cluster_ca_certificate = base64decode(
    data.digitalocean_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate
  )
}

/* Data Sources */

data "digitalocean_kubernetes_cluster" "main" {
  name = "${local.core_resource_name_prefix}-k8s-cluster"
}

data "digitalocean_database_cluster" "postgres" {
  name = "${local.core_resource_name_prefix}-database-cluster"
}

data "digitalocean_database_cluster" "redis" {
  count = var.use_redis == "true" ? 1 : 0

  name = "${local.core_resource_name_prefix}-redis-cluster"
}

data "digitalocean_spaces_bucket" "postgres_dump" {
  count = local.postgres_dump_enabled ? 1 : 0

  name   = "${local.core_resource_name_prefix}-s3-bucket"
  region = var.s3_region
}

/* Database */

resource "digitalocean_database_user" "postgres" {
  cluster_id = data.digitalocean_database_cluster.postgres.id
  name       = "${local.project_slug}-${var.env_slug}-database-user"
}

resource "digitalocean_database_db" "postgres" {
  cluster_id = data.digitalocean_database_cluster.postgres.id
  name       = "${local.project_slug}-${var.env_slug}-database"
}

resource "digitalocean_database_connection_pool" "postgres" {
  cluster_id = data.digitalocean_database_cluster.postgres.id
  db_name    = digitalocean_database_db.postgres.name
  user       = digitalocean_database_user.postgres.name
  name       = "${local.project_slug}-${var.env_slug}-database-pool"
  mode       = "transaction"
  size       = var.database_connection_pool_size
}

/* Namespace */

resource "kubernetes_namespace_v1" "main" {
  metadata {
    name = "${local.project_slug}-${var.env_slug}"
  }
}

/* Routing */

module "routing" {
  source = "../modules/kubernetes/routing"

  namespace = local.namespace

  project_host = local.project_host

  stack_slug = var.stack_slug

  basic_auth_enabled  = var.basic_auth_enabled
  basic_auth_username = var.basic_auth_username
  basic_auth_password = var.basic_auth_password

  backend_middlewares  = var.backend_middlewares
  backend_service_port = var.backend_service_port
  backend_service_slug = var.backend_service_slug

  frontend_middlewares  = var.frontend_middlewares
  frontend_service_port = var.frontend_service_port
  frontend_service_slug = var.frontend_service_slug

  media_storage = local.media_storage

  tls_certificate_crt = var.tls_certificate_crt
  tls_certificate_key = var.tls_certificate_key
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

resource "kubernetes_secret_v1" "database_url" {
  metadata {
    name      = "database-url"
    namespace = local.namespace
  }
  data = {
    DATABASE_URL = digitalocean_database_connection_pool.postgres.private_uri
  }
}

resource "kubernetes_secret_v1" "cache_url" {
  count = var.use_redis == "true" ? 1 : 0

  metadata {
    name      = "cache-url"
    namespace = local.namespace
  }
  data = {
    CACHE_URL = data.digitalocean_database_cluster.redis[0].private_uri
  }
}

/* Cron Jobs */

module "database_dump_cronjob" {
  count = local.postgres_dump_enabled ? 1 : 0

  source = "../modules/kubernetes/database-dump-cronjob"

  namespace = local.namespace

  media_storage = local.media_storage

  s3_region      = var.s3_region
  s3_access_id   = var.s3_access_id
  s3_secret_key  = var.s3_secret_key
  s3_host        = local.s3_host
  s3_bucket_name = local.s3_bucket_name
}
