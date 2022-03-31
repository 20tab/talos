locals {
  project_slug = "{{ cookiecutter.project_slug }}"

  resource_name_prefix = var.stack_slug == "main" ? local.project_slug : "${local.project_slug}-${var.stack_slug}"

  stacks = jsondecode(<<EOF
{{ cookiecutter.stacks|tojson(2) }}
EOF
  )
  envs = local.stacks[var.stack_slug]

  monitoring_enabled = var.monitoring_url != "" && var.stack_slug == "main"
  monitoring_host    = local.monitoring_enabled ? regexall("https?://([^/]+)", var.monitoring_url)[0][0] : ""
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
      version = "2.5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.9.0"
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
  name = "${local.resource_name_prefix}-k8s-cluster"
}

data "digitalocean_domain" "main" {
  count = var.project_domain != "" ? 1 : 0

  name = var.project_domain
}

/* Certificate */

resource "digitalocean_certificate" "ssl_cert" {
  count = var.project_domain != "" ? 1 : 0

  name = "${local.project_slug}-${var.stack_slug}-lets-encrypt-certificate"
  type = "lets_encrypt"
  domains = concat(
    [for k, v in local.envs : "${v.prefix}.${var.project_domain}"],
    local.monitoring_enabled && var.monitoring_domain_prefix != "" ? [var.monitoring_domain_prefix] : []
  )
}

/* Traefik */

module "traefik" {
  source = "../modules/kubernetes/traefik"

  letsencrypt_certificate_email = var.letsencrypt_certificate_email
  load_balancer_annotations = merge(
    {
      "service.beta.kubernetes.io/do-loadbalancer-name" = "${local.resource_name_prefix}-load-balancer"
    },
    var.project_domain != "" ? {
      "service.beta.kubernetes.io/do-loadbalancer-protocol"                         = "http"
      "service.beta.kubernetes.io/do-loadbalancer-tls-ports"                        = "443"
      "service.beta.kubernetes.io/do-loadbalancer-certificate-id"                   = digitalocean_certificate.ssl_cert[0].uuid
      "service.beta.kubernetes.io/do-loadbalancer-disable-lets-encrypt-dns-records" = "false"
      "service.beta.kubernetes.io/do-loadbalancer-redirect-http-to-https"           = "true"
    } : {}
  )
  ssl_enabled = var.project_domain == "" && var.letsencrypt_certificate_email != ""
}

/* Reloader */

resource "helm_release" "reloader" {
  name       = "reloader"
  chart      = "reloader"
  repository = "https://stakater.github.io/stakater-charts"
}

/* Monitoring */

module "monitoring" {
  count = local.monitoring_enabled ? 1 : 0

  source = "../modules/kubernetes/monitoring"

  grafana_user     = var.grafana_user
  grafana_password = var.grafana_password
  grafana_version  = var.grafana_version

  host = local.monitoring_host

  depends_on = [
    module.traefik
  ]
}
