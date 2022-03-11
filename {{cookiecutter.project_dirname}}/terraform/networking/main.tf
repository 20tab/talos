locals {
  project_slug = "{{ cookiecutter.project_slug }}"

  resource_name = var.stack_slug == "main" ? local.project_slug : "${local.project_slug}-${var.stack_slug}"

  stacks = jsondecode(<<EOF
{{ cookiecutter.stacks|tojson(2) }}
EOF
  )
  envs = local.stacks[var.stack_slug]
}

terraform {
  backend "http" {
  }

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "2.4.1"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.8.0"
    }
  }
}

/* Providers */

provider "digitalocean" {
  token = var.digitalocean_token
}

provider "helm" {
  kubernetes {
    host  = data.digitalocean_kubernetes_cluster.main.endpoint
    token = data.digitalocean_kubernetes_cluster.main.kube_config[0].token
    cluster_ca_certificate = base64decode(
      data.digitalocean_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate
    )
  }
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

  name    = "${local.project_slug}-${var.stack_slug}-lets-encrypt-certificate"
  type    = "lets_encrypt"
  domains = [for k, v in local.envs : "${v.prefix}.${var.project_domain}"]
}

/* Traefik */

resource "helm_release" "traefik" {
  name             = "traefik"
  chart            = "traefik"
  namespace        = "traefik"
  create_namespace = true
  repository       = "https://helm.traefik.io/traefik"
  timeout          = 900

  values = [
    yamlencode(
      {
        service = {
          enabled = "true"
          type    = "LoadBalancer"
          annotations = merge(
            {
              "service.beta.kubernetes.io/do-loadbalancer-name" = "${local.resource_name}-load-balancer"
            },
            var.project_domain != "" ? {
              "service.beta.kubernetes.io/do-loadbalancer-protocol"                         = "http"
              "service.beta.kubernetes.io/do-loadbalancer-tls-ports"                        = "443"
              "service.beta.kubernetes.io/do-loadbalancer-certificate-id"                   = digitalocean_certificate.ssl_cert[0].uuid
              "service.beta.kubernetes.io/do-loadbalancer-disable-lets-encrypt-dns-records" = "true"
              "service.beta.kubernetes.io/do-loadbalancer-redirect-http-to-https"           = "true"
            } : {}
          )
        }
        api = {}
        entryPoints = {
          web = {
            address = ":80"
          }
          websecure = {
            address = ":443"
          }
        }
        log = {
          level = "DEBUG"
        }
        providers = {
          kubernetesIngress = {
            enabled = "true"
          }
          kubernetesIngressRoute = {
            enabled = "true"
          }
        }
      }
    )
  ]
}

/* Reloader */

resource "helm_release" "reloader" {
  name       = "reloader"
  chart      = "reloader"
  repository = "https://stakater.github.io/stakater-charts"
}


/* Monitoring stack */

module "monitoring" {
  count = var.use_monitoring == "true" && var.stack_slug == "main" ? 1 : 0

  source = "./monitoring"

  project_domain = var.project_domain

  grafana_user     = var.grafana_user
  grafana_password = var.grafana_password
  grafana_version  = var.grafana_version

  domain_prefix = local.monitoring_prefix

  depends_on = [
    helm_release.traefik
  ]
}