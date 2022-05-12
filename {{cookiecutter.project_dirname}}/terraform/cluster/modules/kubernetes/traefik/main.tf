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
      merge(
        {
          service = {
            enabled     = "true"
            type        = "LoadBalancer"
            annotations = var.load_balancer_annotations
          }
        },
        var.ssl_enabled ? {
          additionalArguments = concat(
            [
              "--entrypoints.web.http.redirections.entryPoint.to=:443",
              "--entrypoints.websecure.http.tls=true",
            ],
            var.letsencrypt_certificate_email != "" ? [
              "--certificatesresolvers.default.acme.tlschallenge",
              "--certificatesresolvers.default.acme.email=${var.letsencrypt_certificate_email}",
              "--certificatesresolvers.default.acme.storage=/data/acme.json",
              "--entrypoints.websecure.http.tls.certResolver=default",
            ] : [],
          )
        } : {}
      )
    )
  ]
}
