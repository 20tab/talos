locals {
  project_slug = "{{ cookiecutter.project_slug }}"

  stack_resources_prefix = var.stack_slug == "main" ? local.project_slug : "${local.project_slug}-${var.stack_slug}"
  env_resources_prefix   = "${local.project_slug}-${var.env_slug}"

  namespace = kubernetes_namespace_v1.main.metadata[0].name

  project_host = regexall("https?://([^/]+)", var.project_url)[0][0]

  backend_paths = toset(
    var.backend_service_slug != "" ? (
      var.frontend_service_slug != "" ? concat(
        ["/admin", "/api", "/static"],
        var.media_storage == "local" ? ["/media"] : []
      ) : ["/"]
    ) : []
  )
  frontend_paths = toset(var.frontend_service_slug != "" ? ["/"] : [])

  basic_auth_enabled = var.basic_auth_enabled == "true" && var.basic_auth_username != "" && var.basic_auth_password != ""

  traefik_middlewares = local.basic_auth_enabled ? [{ "name" : "traefik-basic-auth-middleware" }] : []

  registry_username = coalesce(var.registry_username, "${local.project_slug}-k8s-regcred")

  postgres_dump_enabled = var.env_slug == "prod" && var.media_storage == "s3-digitalocean" && var.s3_bucket_access_id != "" && var.s3_bucket_secret_key != ""
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

  spaces_access_id  = var.s3_bucket_access_id
  spaces_secret_key = var.s3_bucket_secret_key
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
  name = "${local.stack_resources_prefix}-k8s-cluster"
}

data "digitalocean_database_cluster" "postgres" {
  name = "${local.stack_resources_prefix}-database-cluster"
}

data "digitalocean_database_cluster" "redis" {
  count = var.use_redis == "true" ? 1 : 0

  name = "${local.stack_resources_prefix}-redis-cluster"
}

data "digitalocean_spaces_bucket" "postgres_dump" {
  count = local.postgres_dump_enabled ? 1 : 0

  name   = "${local.stack_resources_prefix}-s3-bucket"
  region = var.s3_bucket_region
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
    name = local.env_resources_prefix
  }
}

/* Basic Auth */

resource "kubernetes_secret_v1" "traefik_basic_auth" {
  count = local.basic_auth_enabled ? 1 : 0

  metadata {
    name      = "basic-auth"
    namespace = local.namespace
  }

  data = {
    username = var.basic_auth_username
    password = var.basic_auth_password
  }

  type = "kubernetes.io/basic-auth"
}

resource "kubernetes_manifest" "traefik_basic_auth_middleware" {
  count = local.basic_auth_enabled ? 1 : 0

  manifest = {
    "apiVersion" = "traefik.containo.us/v1alpha1"
    "kind"       = "Middleware"
    "metadata" = {
      "name"      = "traefik-basic-auth-middleware"
      "namespace" = local.namespace
    }
    "spec" = {
      "basicAuth" = {
        "removeHeader" = true
        "secret"       = kubernetes_secret_v1.traefik_basic_auth[0].metadata[0].name
      }
    }
  }
}

/* Traefik Ingress Route */

resource "kubernetes_manifest" "traefik_ingress_route" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "${local.env_resources_prefix}-ingress-route"
      namespace = local.namespace
    }
    spec = merge(
      {
        entryPoints = ["web", "websecure"]
        routes = concat(
          # backend routes
          [
            for path in local.backend_paths : {
              kind        = "Rule"
              match       = "Host(`${local.project_host}`) && PathPrefix(`${path}`)"
              middlewares = local.traefik_middlewares
              services = [
                {
                  name = var.backend_service_slug
                  port = var.backend_service_port
                }
              ]
            }
          ],
          # frontend routes
          [
            for path in local.frontend_paths : {
              kind        = "Rule"
              match       = "Host(`${local.project_host}`) && PathPrefix(`${path}`)"
              middlewares = local.traefik_middlewares
              services = [
                {
                  name = var.frontend_service_slug
                  port = var.frontend_service_port
                }
              ]
            }
          ]
        )
      }
    )
  }
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
    name      = "${local.env_resources_prefix}-database-url"
    namespace = local.namespace
  }

  data = {
    DATABASE_URL = digitalocean_database_connection_pool.postgres.private_uri
  }
}

resource "kubernetes_secret_v1" "cache_url" {
  count = var.use_redis == "true" ? 1 : 0

  metadata {
    name      = "${local.env_resources_prefix}-cache-url"
    namespace = local.namespace
  }

  data = {
    CACHE_URL = data.digitalocean_database_cluster.redis[0].private_uri
  }
}

/* Database dump Cron Job */

resource "kubernetes_secret_v1" "postgres_dump" {
  count = local.postgres_dump_enabled ? 1 : 0

  metadata {
    name      = "${local.project_slug}-postgres-dump"
    namespace = local.namespace
  }

  data = {
    AWS_ACCESS_KEY_ID     = var.s3_bucket_access_id
    AWS_SECRET_ACCESS_KEY = var.s3_bucket_secret_key
    DATABASE_URL          = digitalocean_database_connection_pool.postgres.private_uri
  }
}

resource "kubernetes_config_map_v1" "postgres_dump" {
  count = local.postgres_dump_enabled ? 1 : 0

  metadata {
    name      = "${local.project_slug}-postgres-dump"
    namespace = local.namespace
  }

  data = {
    AWS_S3_BACKUP_PATH      = "backup/postgres"
    AWS_S3_HOST             = "${var.s3_bucket_region}.digitaloceanspaces.com"
    AWS_STORAGE_BUCKET_NAME = data.digitalocean_spaces_bucket.postgres_dump[0].name
  }
}

resource "kubernetes_cron_job_v1" "postgres_dump" {
  count = local.postgres_dump_enabled ? 1 : 0

  metadata {
    name      = "postgresql-dump-cron"
    namespace = local.namespace
  }

  spec {
    schedule = "0 0 * * *"
    job_template {
      metadata {}
      spec {
        template {
          metadata {}
          spec {
            container {
              name    = "postgresql-dump-to-s3"
              image   = "20tab/postgres-dump-restore-to-from-s3:latest"
              command = ["/pg_dump_to_s3.sh"]
              env_from {
                config_map_ref {
                  name = kubernetes_config_map_v1.postgres_dump[0].metadata[0].name
                }
              }
              env_from {
                secret_ref {
                  name = kubernetes_secret_v1.postgres_dump[0].metadata[0].name
                }
              }
            }
            restart_policy = "OnFailure"
          }
        }
      }
    }
  }
}
