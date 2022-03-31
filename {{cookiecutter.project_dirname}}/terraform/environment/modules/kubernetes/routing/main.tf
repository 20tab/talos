locals {
  backend_paths = toset(
    var.backend_service_slug != "" ? (
      var.frontend_service_slug != "" ? concat(
        ["/admin", "/api", "/static"],
        var.media_storage == "local" ? ["/media"] : []
      ) : ["/"]
    ) : []
  )
  frontend_paths = toset(var.frontend_service_slug != "" ? ["/"] : [])

  basic_auth_enabled = alltrue(
    [
      var.basic_auth_enabled == "true",
      var.basic_auth_username != "",
      var.basic_auth_password != ""
    ]
  )

  base_middlewares = local.basic_auth_enabled ? [{ "name" : "traefik-basic-auth-middleware" }] : []
}

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.9.0"
    }
  }
}

/* Basic Auth */

resource "kubernetes_secret_v1" "traefik_basic_auth" {
  count = local.basic_auth_enabled ? 1 : 0

  metadata {
    name      = "basic-auth"
    namespace = var.namespace
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
      "namespace" = var.namespace
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
      name      = "main"
      namespace = var.namespace
    }
    spec = merge(
      {
        entryPoints = ["web", "websecure"]
        routes = concat(
          # backend routes
          [
            for path in local.backend_paths : {
              kind        = "Rule"
              match       = "Host(`${var.project_host}`) && PathPrefix(`${path}`)"
              middlewares = concat(local.base_middlewares, var.backend_middlewares)
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
              match       = "Host(`${var.project_host}`) && PathPrefix(`${path}`)"
              middlewares = concat(local.base_middlewares, var.frontend_middlewares)
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
