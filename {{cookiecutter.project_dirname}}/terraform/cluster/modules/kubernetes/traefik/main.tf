terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
  }
}

resource "helm_release" "traefik" {
  name             = "traefik"
  repository       = "https://traefik.github.io/charts"
  chart            = "traefik"
  version          = var.traefik_helm_chart_version

  namespace        = "traefik"
  create_namespace = true

  timeout          = 900

  values = [
    file("${path.module}/values.yaml"),
    yamlencode(
      {
        service = {
          enabled     = "true"
          type        = "LoadBalancer"
          annotations = var.load_balancer_annotations
        }
      }
    )
  ]
}

/* Cert Manager */

resource "helm_release" "cert_manager" {
  count = var.letsencrypt_certificate_email != "" ? 1 : 0

  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = "1.14.4"

  namespace        = "cert-manager"
  create_namespace = true

  set {
    name  = "installCRDs"
    value = true
  }
}
