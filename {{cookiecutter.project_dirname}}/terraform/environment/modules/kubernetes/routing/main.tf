locals {
  basic_auth_ready = alltrue(
    [
      var.basic_auth_username != "",
      var.basic_auth_password != ""
    ]
  )

  domains           = [for i in var.subdomains : i == "" ? var.project_domain : "${i}.${var.project_domain}"]
  monitoring_domain = var.monitoring_subdomain != "" ? "${var.monitoring_subdomain}.${var.project_domain}" : ""

  traefik_hosts = join(", ", [for i in local.domains : "`${i}`"])

  secondary_domains_traefik_hosts = join(", ", [for i in var.secondary_domains : "`${i}`"])

  http_redirect_traefik_hosts = join(", ", [for i in concat(
    local.domains,
    var.secondary_domains,
    local.monitoring_domain != "" ? [local.monitoring_domain] : [],
  ) : "`${i}`"])

  base_middlewares = var.basic_auth_enabled && local.basic_auth_ready ? [{ "name" : "traefik-basic-auth" }] : []

  letsencrypt_enabled        = var.letsencrypt_certificate_email != ""
  manual_certificate_enabled = var.tls_certificate_crt != "" && var.tls_certificate_key != ""
  tls_enabled                = local.manual_certificate_enabled || local.letsencrypt_enabled

  tls_secret_name = local.tls_enabled ? "tls-certificate" : ""
}

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.13"
    }
  }
}

/* Basic Auth */

resource "kubernetes_secret_v1" "traefik_basic_auth" {
  count = var.basic_auth_enabled && local.basic_auth_ready ? 1 : 0

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
  count = var.basic_auth_enabled && local.basic_auth_ready ? 1 : 0

  manifest = {
    "apiVersion" = "traefik.containo.us/v1alpha1"
    "kind"       = "Middleware"
    "metadata" = {
      "name"      = "traefik-basic-auth"
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
  count = local.manual_certificate_enabled ? 1 : 0

  metadata {
    name      = local.tls_secret_name
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
      secretName = local.tls_secret_name
      issuerRef = {
        name = "letsencrypt"
        kind = "Issuer"
      }
      dnsNames = concat(
        local.domains, var.secondary_domains, local.monitoring_domain != "" ? [local.monitoring_domain] : []
      )
    }
  }
}

/* Main Ingress Route */

resource "kubernetes_manifest" "main_ingress_route" {
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
        )
      },
      local.tls_enabled ? {
        tls = {
          secretName = local.tls_secret_name
        }
      } : {}
    )
  }
}

/* Monitoring Ingress Route */

resource "kubernetes_manifest" "monitoring_ingress_route" {
  count = local.monitoring_domain != "" ? 1 : 0

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "monitoring"
      namespace = "log-storage"
    }
    spec = merge(
      {
        entryPoints = local.tls_enabled ? ["websecure"] : ["web"]
        routes = [
          {
            kind  = "Rule"
            match = "Host(`${local.monitoring_domain}`)"
            services = [
              {
                name = "grafana"
                port = 80
              }
            ]
          }
        ]
      },
      local.tls_enabled ? {
        tls = {
          secretName = local.tls_secret_name
        }
      } : {}
    )
  }
}

/* Metrics Ingress Route */

resource "kubernetes_secret_v1" "metrics_basic_auth" {
  count = local.basic_auth_ready ? 1 : 0

  metadata {
    name      = "metrics-basic-auth-${var.env_slug}"
    namespace = "kube-system"
  }

  data = {
    username = var.basic_auth_username
    password = var.basic_auth_password
  }

  type = "kubernetes.io/basic-auth"
}

resource "kubernetes_manifest" "metrics_basic_auth_middleware" {
  count = local.basic_auth_ready ? 1 : 0

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "metrics-basic-auth-${var.env_slug}"
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

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "metrics-${var.env_slug}"
      namespace = "kube-system"
    }
    spec = merge(
      {
        entryPoints = local.tls_secret_name != "" ? ["websecure"] : ["web"]
        routes = concat(
          local.basic_auth_ready ? [
            {
              kind        = "Rule"
              match       = "Host(${local.traefik_hosts}) && PathPrefix(`/metrics`)"
              middlewares = [{ "name" : "metrics-basic-auth-${var.env_slug}" }]
              services = [
                {
                  name = "kube-state-metrics"
                  port = 8080
                }
              ]
          }] : [],
          [{
            kind        = "Rule"
            match       = "Host(${local.traefik_hosts}) && PathPrefix(`/healthz`)"
            middlewares = []
            services = [
              {
                name = "kube-state-metrics"
                port = 8080
              }
            ]
            }
        ])
      },
      local.tls_secret_name != "" ? {
        tls = {
          secretName = local.tls_secret_name
        }
      } : {}
    )
  }
}

/* HTTPS Redirect */

resource "kubernetes_manifest" "middleware_redirect_to_https" {
  count = local.tls_enabled ? 1 : 0

  manifest = {
    apiVersion = "traefik.io/v1alpha1"
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

resource "kubernetes_manifest" "ingressroute_redirect_to_https" {
  count = local.tls_enabled ? 1 : 0

  manifest = {
    apiVersion = "traefik.io/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "redirect-to-https"
      namespace = var.namespace
    }
    spec = merge(
      {
        entryPoints = ["web"]
        routes = [
          {
            kind  = "Rule"
            match = "Host(${local.http_redirect_traefik_hosts})"
            middlewares = [
              { name = "redirect-to-https" }
            ]
            services = [
              {
                name = coalesce(var.frontend_service_slug, var.backend_service_slug)
                port = coalesce(var.frontend_service_port, var.backend_service_port)
              }
            ]
          }
        ]
      }
    )
  }
}

/* Secondary Domains Redirect */

resource "kubernetes_manifest" "middleware_secondary_domains_redirect" {
  manifest = {
    apiVersion = "traefik.io/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "redirect-secondary-domains"
      namespace = var.namespace
    }
    spec = {
      redirectRegex = {
        regex = join(
          "", [
            "^(https?)://(?:",
            join("|", [for i in var.secondary_domains : replace(i, ".", "\\.")]),
            ")(.*)$"
          ]
        )
        replacement = "$1://${local.domains[0]}$2"
      }
    }
  }

  computed_fields = ["metadata.labels.domain", "metadata.name"]
}

resource "kubernetes_manifest" "ingressroute_secondary_domains_redirect" {
  manifest = {
    apiVersion = "traefik.io/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "redirect-secondary-domains"
      namespace = var.namespace
    }
    spec = merge(
      {
        entryPoints = local.tls_enabled ? ["websecure"] : ["web"]
        routes = [
          {
            kind  = "Rule"
            match = "Host(${local.secondary_domains_traefik_hosts})"
            middlewares = [
              { name = "redirect-secondary-domains" },
            ]
            services = [
              {
                name = coalesce(var.frontend_service_slug, var.backend_service_slug)
                port = coalesce(var.frontend_service_port, var.backend_service_port)
              }
            ]
          }
        ]
      },
      local.letsencrypt_enabled ? {
        tls = {
          secretName = "tls-letsencrypt"
        }
      } : {}
    )
  }
}
