locals {
  base_resource_name_prefix = var.stack_slug == "main" ? var.project_slug : "${var.project_slug}-${var.stack_slug}"

  namespace = kubernetes_namespace_v1.main.metadata[0].name

  domain_id = var.create_dns_records ? var.create_domain ? digitalocean_domain.main[0].id : data.digitalocean_domain.main[0].id : ""

  s3_host        = var.digitalocean_spaces_bucket_available ? "${var.s3_region}.digitaloceanspaces.com" : var.s3_host
  s3_bucket_name = var.digitalocean_spaces_bucket_available ? "${local.base_resource_name_prefix}-s3-bucket" : var.s3_bucket_name

  postgres_dump_enabled = alltrue(
    [
      var.database_dumps_enabled,
      var.env_slug == "prod",
      var.s3_region != "",
      var.s3_access_id != "",
      var.s3_secret_key != "",
      local.s3_bucket_name != "",
      local.s3_host != "",
    ]
  )
}

terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.22"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.6"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.13"
    }
  }
}

/* Providers */

provider "digitalocean" {
  token = var.digitalocean_token

  spaces_access_id  = var.s3_access_id
  spaces_secret_key = var.s3_secret_key
}

provider "helm" {
  kubernetes {
    host  = data.digitalocean_kubernetes_cluster.main.endpoint
    token = data.digitalocean_kubernetes_cluster.main.kube_config[0].token
    cluster_ca_certificate = base64decode(
      data.digitalocean_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate
    )
  }
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
  count = var.use_redis ? 1 : 0

  name = "${local.base_resource_name_prefix}-redis-cluster"
}

data "digitalocean_spaces_bucket" "postgres_dump" {
  count = local.postgres_dump_enabled ? 1 : 0

  name   = "${local.base_resource_name_prefix}-s3-bucket"
  region = var.s3_region
}

data "digitalocean_loadbalancer" "main" {
  name = "${local.base_resource_name_prefix}-load-balancer"
}

data "digitalocean_domain" "main" {
  count = var.create_dns_records && !var.create_domain ? 1 : 0

  name = var.project_domain
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

/* Domain */

resource "digitalocean_domain" "main" {
  count = var.create_dns_records && var.create_domain ? 1 : 0

  name = var.project_domain
}

/* DNS records */

resource "digitalocean_record" "main" {
  for_each = toset(var.create_dns_records ? [for i in var.subdomains : i == "" ? "@" : i] : [])

  domain = local.domain_id
  type   = "A"
  name   = each.key
  value  = data.digitalocean_loadbalancer.main.ip
}

resource "digitalocean_record" "monitoring" {
  count = var.create_dns_records && var.monitoring_subdomain != "" ? 1 : 0

  domain = local.domain_id
  type   = "A"
  name   = var.monitoring_subdomain
  value  = data.digitalocean_loadbalancer.main.ip
}

/* Namespace */

resource "kubernetes_namespace_v1" "main" {
  metadata {
    name = "${var.project_slug}-${var.env_slug}"
  }
}

/* Monitoring */

module "monitoring" {
  count = var.monitoring_subdomain != "" ? 1 : 0

  source = "../modules/kubernetes/monitoring"

  grafana_user                = var.grafana_user
  grafana_password            = var.grafana_password
  grafana_persistence_enabled = var.grafana_persistence_enabled
  grafana_version             = var.grafana_version
}

/* Routing */

module "routing" {
  source = "../modules/kubernetes/routing"

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


/* Routing Metrics */

module "metrics" {
  count = var.stack_slug == "main" && var.env_slug == "prod" ? 1 : 0

  source = "../modules/kubernetes/metrics"

  project_domain = var.project_domain

  basic_auth_username = var.basic_auth_username
  basic_auth_password = var.basic_auth_password

  tls_secret_name = module.routing.tls_secret_name
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
    DATABASE_URL = replace(digitalocean_database_connection_pool.postgres.private_uri, "/^postgresql:///", var.use_postgis ? "postgis://" : "postgresql://")
  }
}

resource "kubernetes_secret_v1" "cache_url" {
  count = var.use_redis ? 1 : 0

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

  database_url = digitalocean_database_connection_pool.postgres.private_uri
}
