locals {
  backend_paths = var.backend_service_slug != "" ? (
    var.frontend_service_slug != "" ? concat(
      ["/admin", "/api", "/static"],
      var.media_storage == "local" ? ["/media"] : []
    ) : ["/"]
  ) : []
  frontend_paths = var.frontend_service_slug != "" ? ["/"] : []

  resource_name = var.stack_slug == "main" ? var.project_slug : "${var.project_slug}-${var.stack_slug}"
}

terraform {
  backend "local" {
  }

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.6.0"
    }
  }
}

provider "digitalocean" {
  token = var.digitalocean_token
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
  name = "${local.resource_name}-k8s-cluster"
}

data "digitalocean_domain" "main" {
  count = var.project_domain != "" ? 1 : 0

  name = var.project_domain
}

/* Certificate */

resource "digitalocean_certificate" "ssl_cert" {
  count = var.project_domain != "" ? 1 : 0

  name    = "${var.project_slug}-lets-encrypt-certificate"
  type    = "lets_encrypt"
  domains = ["*.${var.project_domain}"]
}

/* RBAC */

resource "kubernetes_cluster_role" "traefik_ingress_controller" {
  metadata {
    name = "${local.resource_name}-traefik-ingress-controller"
  }

  rule {
    api_groups = [""]
    resources  = ["services", "endpoints", "secrets"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["extensions", "networking.k8s.io"]
    resources  = ["ingresses", "ingressclasses"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["extensions"]
    resources  = ["ingresses/status"]
    verbs      = ["update"]
  }
}

resource "kubernetes_service_account" "traefik_ingress_controller" {
  metadata {
    name = "${local.resource_name}-traefik-ingress-controller"
  }
}

resource "kubernetes_cluster_role_binding" "traefik_ingress_controller" {
  metadata {
    name = "${local.resource_name}-traefik-ingress-controller"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "traefik-ingress-controller"
  }
  subject {
    kind      = "ServiceAccount"
    name      = "traefik-ingress-controller"
    namespace = "default"
  }
}

/* Traefik Controller Deployment */

resource "kubernetes_deployment" "traefik_controller" {
  metadata {
    name = "${local.resource_name}-traefik-ingress-controller"
    labels = {
      app   = "traefik"
      stack = var.stack_slug
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app   = "traefik"
        stack = var.stack_slug
      }
    }

    template {
      metadata {
        labels = {
          app   = "traefik"
          stack = var.stack_slug
        }
      }

      spec {
        service_account_name = "traefik-ingress-controller"

        container {
          name  = "traefik"
          image = "traefik:v2.5"

          args = [
            "--providers.kubernetesingress",
            "--entrypoints.web.address=:80",
            "--entrypoints.websecure.address=:443"
          ]

          port {
            name           = "web"
            container_port = 80
          }

          port {
            name           = "websecure"
            container_port = 443
          }
        }
      }
    }
  }
}

/* Load Balancer */

resource "kubernetes_service" "traefik_load_balancer" {
  metadata {
    name = "${local.resource_name}-load-balancer"
    annotations = merge(
      {
        "service.beta.kubernetes.io/do-loadbalancer-name" = "${local.resource_name}-load-balancer"
      },
      var.project_domain != "" ? {
        "service.beta.kubernetes.io/do-loadbalancer-redirect-http-to-https" = "true"
        "service.beta.kubernetes.io/do-loadbalancer-protocol"               = "http"
        "service.beta.kubernetes.io/do-loadbalancer-tls-ports"              = "443"
        "service.beta.kubernetes.io/do-loadbalancer-certificate-id"         = "${digitalocean_certificate.ssl_cert[0].id}"
      } : {}
    )
  }

  spec {
    type = "LoadBalancer"
    selector = {
      app   = "traefik"
      stack = var.stack_slug
    }

    port {
      name        = "web"
      protocol    = "TCP"
      port        = 80
      target_port = 80
    }

    port {
      name        = "websecure"
      protocol    = "TCP"
      port        = 443
      target_port = 443
    }
  }
}

/* Ingress */

resource "kubernetes_ingress" "main" {
  for_each = var.stack_envs

  metadata {
    name      = "${local.resource_name}-ingress"
    namespace = "${var.project_slug}-${each.key}"
    annotations = {
      "kubernetes.io/ingress.class"                      = "traefik"
      "traefik.ingress.kubernetes.io/router.entrypoints" = "websecure"
    }
  }

  spec {
    rule {
      host = replace(each.value.url, "/https?:///", "")

      http {

        dynamic "path" {
          for_each = toset(local.backend_paths)
          content {
            path = each.key

            backend {
              service_name = var.backend_service_slug
              service_port = var.backend_service_port
            }

          }
        }

        dynamic "path" {
          for_each = toset(local.frontend_paths)
          content {
            path = each.key

            backend {
              service_name = var.frontend_service_slug
              service_port = var.frontend_service_port
            }

          }
        }
      }
    }
  }
}

/* DNS Records */

resource "digitalocean_record" "main" {
  for_each = var.project_domain != "" ? var.stack_envs : {}

  domain = data.digitalocean_domain.main[0].name
  type   = "A"
  name   = each.value.prefix
  value  = kubernetes_service.traefik_load_balancer.status[0].load_balancer[0].ingress[0].ip
}
