terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "2.5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.9.0"
    }
  }
}

resource "helm_release" "traefik" {
  name             = "traefik"
  chart            = "traefik"
  namespace        = "traefik"
  create_namespace = true
  repository       = "https://helm.traefik.io/traefik"
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
  chart            = "cert-manager"
  namespace        = "cert-manager"
  create_namespace = true
  repository       = "https://charts.jetstack.io"
  version          = "1.7.2"

  set {
    name  = "installCRDs"
    value = true
  }
}
