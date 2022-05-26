terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.9.0"
    }
  }
}

/* Metrics Ingress Route */

resource "kubernetes_secret_v1" "metrics_basic_auth" {
  count = var.stack_slug == "main" && var.basic_auth_ready ? 1 : 0

  metadata {
    name      = "metrics-basic-auth"
    namespace = "kube-system"
  }

  data = {
    username = var.basic_auth_username
    password = var.basic_auth_password
  }

  type = "kubernetes.io/basic-auth"
}

resource "kubernetes_manifest" "metrics_basic_auth_middleware" {
  count = var.stack_slug == "main" && var.basic_auth_ready ? 1 : 0

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "metrics-basic-auth-middleware"
      namespace = "kube-system"
    }
    spec = {
      basicAuth = {
        removeHeader = true
        secret       = kubernetes_secret_v1.metrics_basic_auth[0].metadata[0].name
      }
    }
  }
}

resource "kubernetes_manifest" "metrics_ingress_route" {
  count = var.stack_slug == "main" ? 1 : 0

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "metrics-ingress-route"
      namespace = "kube-system"
    }
    spec = {
      entryPoints = ["web", "websecure"]
      routes = concat(
        var.basic_auth_ready ? [
          {
            kind        = "Rule"
            match       = "Host(`${var.project_host}`) && PathPrefix(`/metrics`)"
            middlewares = [{ "name" : "metrics-basic-auth-middleware" }]
            services = [
              {
                name = "kube-state-metrics"
                port = 8080
              }
            ]
        }] : [],
        [{
          kind        = "Rule"
          match       = "Host(`${var.project_host}`) && PathPrefix(`/healthz`)"
          middlewares = []
          services = [
            {
              name = "kube-state-metrics"
              port = 8080
            }
          ]
          }
      ])
    }
  }
}
