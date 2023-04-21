locals {
  namespace = kubernetes_namespace_v1.main.metadata[0].name

  postgres_dump_enabled = alltrue(
    [
      var.database_dumps_enabled,
      var.env_slug == "prod",
      var.s3_region != "",
      var.s3_access_id != "",
      var.s3_secret_key != "",
      var.s3_bucket_name != "",
    ]
  )
}

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.13"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.6"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
}

/* Providers */

provider "kubernetes" {
  host                   = var.kubernetes_host
  token                  = var.kubernetes_token
  cluster_ca_certificate = base64decode(var.kubernetes_cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = var.kubernetes_host
    token                  = var.kubernetes_token
    cluster_ca_certificate = base64decode(var.kubernetes_cluster_ca_certificate)
  }
}

/* Namespace */

resource "kubernetes_namespace_v1" "main" {
  metadata {
    name = "${var.project_slug}-${var.env_slug}"
  }
}

/* Databases */

module "postgres" {
  source = "../modules/kubernetes/postgres"

  namespace = local.namespace

  postgres_image = var.postgres_image

  database_name = "${var.project_slug}-${var.env_slug}-database"
  database_user = "${var.project_slug}-${var.env_slug}-database-user"

  persistent_volume_capacity       = var.postgres_persistent_volume_capacity
  persistent_volume_claim_capacity = var.postgres_persistent_volume_claim_capacity
  persistent_volume_host_path      = var.postgres_persistent_volume_host_path
}

module "redis" {
  count = var.use_redis ? 1 : 0

  source = "../modules/kubernetes/redis"

  namespace = local.namespace

  redis_image = var.redis_image
}

/* Monitoring */

module "monitoring" {
  count = var.monitoring_subdomain != "" ? 1 : 0

  source = "../modules/kubernetes/monitoring"

  grafana_password            = var.grafana_password
  grafana_persistence_enabled = var.grafana_persistence_enabled
  grafana_user                = var.grafana_user
  grafana_version             = var.grafana_version

  s3_region      = var.s3_region
  s3_access_id   = var.s3_access_id
  s3_secret_key  = var.s3_secret_key
  s3_bucket_name = var.s3_bucket_name
  s3_host        = var.s3_host
}


/* Metrics */

module "metrics" {
  count = var.stack_slug == "main" && var.env_slug == "prod" ? 1 : 0

  source = "../modules/kubernetes/metrics"
}

/* Routing */

module "routing" {
  source = "../modules/kubernetes/routing"

  env_slug  = var.env_slug
  namespace = local.namespace

  project_domain = var.project_domain
  subdomains     = var.subdomains

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

  letsencrypt_certificate_email = var.letsencrypt_certificate_email
  letsencrypt_server            = var.letsencrypt_server
  tls_certificate_crt           = var.tls_certificate_crt
  tls_certificate_key           = var.tls_certificate_key

  monitoring_subdomain = var.monitoring_subdomain
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
    DATABASE_URL = module.postgres.database_url
  }
}

resource "kubernetes_secret_v1" "redis_url" {
  count = var.use_redis ? 1 : 0

  metadata {
    name      = "redis-url"
    namespace = local.namespace
  }
  data = {
    REDIS_URL = module.redis[0].redis_url
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
  s3_host        = var.s3_host
  s3_bucket_name = var.s3_bucket_name

  database_url = module.postgres.database_url
}
