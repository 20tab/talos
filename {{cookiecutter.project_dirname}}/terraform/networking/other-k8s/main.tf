locals {
  project_slug = "{{ cookiecutter.project_slug }}"

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

provider "helm" {
  kubernetes {
    host                   = var.kubernetes_host
    token                  = var.kubernetes_token
    cluster_ca_certificate = base64decode(var.kubernetes_cluster_ca_certificate)
  }
}

provider "kubernetes" {
  host                   = var.kubernetes_host
  token                  = var.kubernetes_token
  cluster_ca_certificate = base64decode(var.kubernetes_cluster_ca_certificate)
}

/* Traefik */

module "traefik" {
  source = "../modules/kubernetes/traefik"

  letsencrypt_certificate_email = var.letsencrypt_certificate_email
  ssl_enabled                   = var.ssl_enabled
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
