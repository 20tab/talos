locals {
  domains           = [for i in var.subdomains : i == "" ? var.project_domain : "${i}.${var.project_domain}"]
  monitoring_domain = var.monitoring_subdomain != "" ? "${var.monitoring_subdomain}.${var.project_domain}" : ""

  traefik_hosts = join(", ", [for i in local.domains : "`${i}`"])

  base_middlewares = var.basic_auth_ready ? [{ "name" : "traefik-basic-auth-middleware" }] : []

  letsencrypt_enabled        = var.letsencrypt_certificate_email != ""
  manual_certificate_enabled = var.tls_certificate_crt != "" && var.tls_certificate_key != ""
  tls_enabled                = local.manual_certificate_enabled || local.letsencrypt_enabled
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
  count = var.basic_auth_ready ? 1 : 0

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
  count = var.basic_auth_ready ? 1 : 0

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

/* HTTPS Redirect */

resource "kubernetes_manifest" "middleware_redirect_to_https" {
  count = local.tls_enabled ? 1 : 0

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "redirect-to-https"
      namespace = var.namespace
    }
    spec = {
      redirectScheme = {
        scheme    = "https"
        permanent = true
      }
    }
  }
}

/* TLS Secret */

resource "kubernetes_secret_v1" "tls" {
  count = local.manual_certificate_enabled ? 1 : 0

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

/* Let's Encrypt Certificate */

resource "kubernetes_manifest" "issuer" {
  count = local.letsencrypt_enabled ? 1 : 0

  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "Issuer"
    metadata = {
      name      = "letsencrypt"
      namespace = var.namespace
    }
    spec = {
      acme = {
        email  = var.letsencrypt_certificate_email
        server = coalesce(var.letsencrypt_server, "https://acme-v02.api.letsencrypt.org/directory")
        privateKeySecretRef = {
          name = "issuer-private-key"
        }
        solvers = [
          {
            http01 = {
              ingress = {
                class = "traefik-cert-manager"
              }
            }
          }
        ]
      }
    }
  }
}

resource "kubernetes_manifest" "certificate" {
  count = local.letsencrypt_enabled ? 1 : 0

  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "Certificate"
    metadata = {
      name      = "letsencrypt"
      namespace = var.namespace
    }
    spec = {
      secretName = "tls-certificate"
      issuerRef = {
        name = "letsencrypt"
        kind = "Issuer"
      }
      dnsNames = concat(
        local.domains, local.monitoring_domain != "" ? [local.monitoring_domain] : []
      )
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
        entryPoints = local.tls_enabled ? ["websecure"] : ["web"]
        routes = concat(
          # frontend routes
          [
            for path in toset(var.frontend_service_paths) : {
              kind  = "Rule"
              match = "Host(${local.traefik_hosts}) && PathPrefix(`${path}`)"
              middlewares = concat(
                local.base_middlewares,
                [for i in var.frontend_service_extra_middlewares : { name = i }],
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
              match = "Host(${local.traefik_hosts}) && PathPrefix(`${path}`)"
              middlewares = concat(
                local.base_middlewares,
                [for i in var.backend_service_extra_middlewares : { name = i }],
              )
              services = [
                {
                  name = var.backend_service_slug
                  port = var.backend_service_port
                }
              ]
            }
          ],
          # monitoring rule
          local.monitoring_domain != "" ? [
            {
              kind  = "Rule"
              match = "Host(`${local.monitoring_domain}`) && PathPrefix(`/`)"
              services = [
                {
                  name = "grafana"
                  port = 80
                }
              ]
            }
          ] : []
        )
      },
      local.tls_enabled ? {
        tls = {
          secretName = "tls-certificate"
        }
      } : {}
    )
  }
}
