locals {
  basic_auth_enabled = alltrue(
    [
      var.basic_auth_enabled == "true",
      var.basic_auth_username != "",
      var.basic_auth_password != ""
    ]
  )

  base_middlewares = local.basic_auth_enabled ? [{ "name" : "traefik-basic-auth-middleware" }] : []

  tls_enabled = var.tls_certificate_crt != "" && var.tls_certificate_key != ""
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

/* TLS Secret */

resource "kubernetes_secret_v1" "tls" {
  count = local.tls_enabled ? 1 : 0

  metadata {
    name      = "tls-certificate"
    namespace = var.namespace
  }

  data = {
    "tls.crt" = base64decode(var.tls_certificate_crt)
    "tls.key" = base64decode(var.tls_certificate_key)
  }

  type = "kubernetes.io/tls"
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
          # frontend routes
          [
            for path in toset(var.frontend_service_paths) : {
              kind  = "Rule"
              match = "Host(`${var.project_host}`) && PathPrefix(`${path}`)"
              middlewares = concat(
                local.base_middlewares,
                var.frontend_service_extra_middlewares,
              )
              services = [
                {
                  name = var.frontend_service_slug
                  port = var.frontend_service_port
                }
              ]
            }
          ],
          # backend routes
          [
            for path in toset(var.backend_service_paths) : {
              kind  = "Rule"
              match = "Host(`${var.project_host}`) && PathPrefix(`${path}`)"
              middlewares = concat(
                local.base_middlewares,
                var.backend_service_extra_middlewares,
              )
              services = [
                {
                  name = var.backend_service_slug
                  port = var.backend_service_port
                }
              ]
            }
          ]
        )
      },
      local.tls_enabled ? {
        tls = {
          secretName = kubernetes_secret_v1.tls[0].metadata[0].name
        }
      } : {}
    )
  }
}
