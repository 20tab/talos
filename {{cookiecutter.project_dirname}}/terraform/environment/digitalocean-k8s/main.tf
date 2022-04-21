locals {
  base_resource_name_prefix = var.stack_slug == "main" ? var.project_slug : "${var.project_slug}-${var.stack_slug}"

  namespace = kubernetes_namespace_v1.main.metadata[0].name

  project_host = regexall("https?://([^/]+)", var.project_url)[0][0]

  s3_host        = var.digitalocean_spaces_bucket_available ? "https://${var.s3_region}.digitaloceanspaces.com" : var.s3_host
  s3_bucket_name = var.digitalocean_spaces_bucket_available ? "${local.base_resource_name_prefix}-s3-bucket" : var.s3_bucket_name

  postgres_dump_enabled = alltrue(
    [
      var.database_dumps_enabled,
      var.env_slug == "prod",
      var.s3_region != "",
      var.s3_access_id != "",
      var.s3_secret_key != "",
      local.s3_host != "" || local.s3_bucket_name != "",
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
  name = "${local.base_resource_name_prefix}-k8s-cluster"
}

data "digitalocean_database_cluster" "postgres" {
  name = "${local.base_resource_name_prefix}-database-cluster"
}

data "digitalocean_database_cluster" "redis" {
  count = var.use_redis == "true" ? 1 : 0

  name = "${local.base_resource_name_prefix}-redis-cluster"
}

data "digitalocean_spaces_bucket" "postgres_dump" {
  count = local.postgres_dump_enabled ? 1 : 0

  name   = "${local.base_resource_name_prefix}-s3-bucket"
  region = var.s3_region
}

/* Database */

resource "digitalocean_database_user" "postgres" {
  cluster_id = data.digitalocean_database_cluster.postgres.id
  name       = "${var.project_slug}-${var.env_slug}-database-user"
}

resource "digitalocean_database_db" "postgres" {
  cluster_id = data.digitalocean_database_cluster.postgres.id
  name       = "${var.project_slug}-${var.env_slug}-database"
}

resource "digitalocean_database_connection_pool" "postgres" {
  cluster_id = data.digitalocean_database_cluster.postgres.id
  db_name    = digitalocean_database_db.postgres.name
  user       = digitalocean_database_user.postgres.name
  name       = "${var.project_slug}-${var.env_slug}-database-pool"
  mode       = "transaction"
  size       = var.database_connection_pool_size
}

/* Namespace */

resource "kubernetes_namespace_v1" "main" {
  metadata {
    name = "${var.project_slug}-${var.env_slug}"
  }
}

/* Routing */

module "routing" {
  source = "../modules/kubernetes/routing"

  namespace = local.namespace

  project_host = local.project_host

  basic_auth_enabled  = var.basic_auth_enabled
  basic_auth_username = var.basic_auth_username
  basic_auth_password = var.basic_auth_password

  backend_service_extra_middlewares = var.backend_service_extra_traefik_middlewares
  backend_service_slug              = var.backend_service_slug
  backend_service_paths             = var.backend_service_paths
  backend_service_port              = var.backend_service_port

  frontend_service_extra_middlewares = var.frontend_service_extra_traefik_middlewares
  frontend_service_slug              = var.frontend_service_slug
  frontend_service_paths             = var.frontend_service_paths
  frontend_service_port              = var.frontend_service_port

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
          auth = "${base64encode("${var.registry_username}:${var.registry_password}")}"
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
    CACHE_URL = "${data.digitalocean_database_cluster.redis[0].private_uri}?key_prefix=${var.env_slug}"
  }
}

/* Cron Jobs */

module "database_dump_cronjob" {
  count = local.postgres_dump_enabled ? 1 : 0

  source = "../modules/kubernetes/database-dump-cronjob"

  namespace = local.namespace

  s3_region      = var.s3_region
  s3_access_id   = var.s3_access_id
  s3_secret_key  = var.s3_secret_key
  s3_host        = local.s3_host
  s3_bucket_name = local.s3_bucket_name
}
