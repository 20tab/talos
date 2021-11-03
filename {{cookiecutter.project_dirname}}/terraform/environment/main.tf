locals {
  project_slug = "{{ cookiecutter.project_slug }}"

  backend_service_slug  = "{{ cookiecutter.backend_service_slug }}"
  frontend_service_slug = "{{ cookiecutter.frontend_service_slug }}"

  backend_paths = local.backend_service_slug != "" ? (
    local.frontend_service_slug != "" ? concat(
      ["/admin", "/api", "/static"],
      var.media_storage == "local" ? ["/media"] : []
    ) : ["/"]
  ) : []
  frontend_paths = local.frontend_service_slug != "" ? ["/"] : []

  registry_username = coalesce(var.registry_username, "${local.project_slug}-k8s-regcred")

  stack_resource_name = var.stack_slug == "main" ? local.project_slug : "${local.project_slug}-${var.stack_slug}"
  env_resource_name   = "${local.project_slug}-${var.env_slug}"

  namespace = kubernetes_namespace.main.metadata[0].name
}

terraform {
  backend "http" {
  }

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    # gitlab = {
    #   source  = "gitlabhq/gitlab"
    #   version = "3.7.0"
    # }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.6.0"
    }
  }
}

/* Providers */

provider "digitalocean" {
  token = var.digitalocean_token
}

# provider "gitlab" {
#   token = var.gitlab_token
# }

provider "kubernetes" {
  host  = data.digitalocean_kubernetes_cluster.main.endpoint
  token = data.digitalocean_kubernetes_cluster.main.kube_config[0].token
  cluster_ca_certificate = base64decode(
    data.digitalocean_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate
  )
}

/* Data Sources */

data "digitalocean_kubernetes_cluster" "main" {
  name = "${local.stack_resource_name}-k8s-cluster"
}

data "digitalocean_database_cluster" "main" {
  name = "${local.stack_resource_name}-database-cluster"
}

data "digitalocean_domain" "main" {
  count = var.project_domain != "" ? 1 : 0

  name = var.project_domain
}

data "digitalocean_loadbalancer" "main" {
  name = "${local.stack_resource_name}-load-balancer"
}

/* Database */

resource "digitalocean_database_user" "main" {
  cluster_id = data.digitalocean_database_cluster.main.id
  name       = "${local.project_slug}-${var.env_slug}-database-user"
}

resource "digitalocean_database_db" "main" {
  cluster_id = data.digitalocean_database_cluster.main.id
  name       = "${local.project_slug}-${var.env_slug}-database"
}

resource "digitalocean_database_connection_pool" "db-production-pool" {
  cluster_id = data.digitalocean_database_cluster.main.id
  db_name    = digitalocean_database_db.main.name
  user       = digitalocean_database_user.main.name
  name       = "${local.project_slug}-${var.env_slug}-database-pool"
  mode       = "transaction"
  size       = var.database_connection_pool_size
}

/* Namespace */

resource "kubernetes_namespace" "main" {
  metadata {
    name = local.env_resource_name
  }
}

/* DNS Records */

resource "digitalocean_record" "main" {
  count = var.project_domain != "" ? 1 : 0

  domain = data.digitalocean_domain.main[0].name
  type   = "A"
  name   = var.domain_prefix
  value  = data.digitalocean_loadbalancer.main.ip
}

/* Ingress */

resource "kubernetes_ingress" "main" {
  metadata {
    name      = "${local.env_resource_name}-ingress"
    namespace = local.namespace
    annotations = {
      "kubernetes.io/ingress.class"                      = "traefik"
      "traefik.ingress.kubernetes.io/router.entrypoints" = var.project_domain == "" ? "web" : "websecure"
    }
  }

  spec {
    rule {
      host = regexall("https?://([^/]+)", var.project_url)[0][0]

      http {

        dynamic "path" {
          for_each = toset(local.backend_paths)
          content {
            path = path.key

            backend {
              service_name = local.backend_service_slug
              service_port = var.backend_service_port
            }
          }
        }

        dynamic "path" {
          for_each = toset(local.frontend_paths)
          content {
            path = path.key

            backend {
              service_name = local.frontend_service_slug
              service_port = var.frontend_service_port
            }
          }
        }
      }
    }
  }
}

/* Regcred */

resource "kubernetes_secret" "regcred" {
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

/* Gitlab Variables */
