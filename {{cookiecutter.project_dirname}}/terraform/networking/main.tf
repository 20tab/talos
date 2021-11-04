locals {
  project_slug = "{{ cookiecutter.project_slug }}"

  resource_name = var.stack_slug == "main" ? local.project_slug : "${local.project_slug}-${var.stack_slug}"
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
      version = "2.6.0"
    }
  }
}

/* Providers */

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
  count = var.stack_slug == "main" && var.project_domain != "" ? 1 : 0

  name    = "${local.project_slug}-lets-encrypt-certificate"
  type    = "lets_encrypt"
  domains = ["*.${var.project_domain}"]
}

/* RBAC */

resource "kubernetes_cluster_role" "traefik_ingress_controller" {
  metadata {
    name = "traefik-ingress-controller"
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
    name = "traefik-ingress-controller"
  }
}

resource "kubernetes_cluster_role_binding" "traefik_ingress_controller" {
  metadata {
    name = "traefik-ingress-controller"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.traefik_ingress_controller.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.traefik_ingress_controller.metadata[0].name
    namespace = "default"
  }
}

/* Traefik Controller Deployment */

resource "kubernetes_deployment" "traefik_controller" {
  metadata {
    name = "traefik-ingress-controller"
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
        service_account_name = kubernetes_service_account.traefik_ingress_controller.metadata[0].name

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
        "service.beta.kubernetes.io/do-loadbalancer-certificate-id"         = "${data.digitalocean_certificate.ssl_cert[0].uuid}"
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
