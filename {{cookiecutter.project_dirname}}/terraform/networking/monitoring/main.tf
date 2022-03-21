locals {
  project_slug = "{{ cookiecutter.project_slug }}"

  stack_resource_name = var.stack_slug == "main" ? local.project_slug : "${local.project_slug}-${var.stack_slug}"
  
  domain_prefix = "logs"

  grafana_domain = var.grafana_domain != "" ? var.grafana_domain :  "${local.domain_prefix}.${var.project_domain}"

}

/* Data Sources */

data "digitalocean_domain" "main" {
  count = var.project_domain != "" ? 1 : 0

  name = var.project_domain
}

data "digitalocean_loadbalancer" "main" {
  name = "${local.stack_resource_name}-load-balancer"
}

/* Kube State Metrics */

resource "helm_release" "kube_state_metrics" {
  name       = "kube-state-metrics"
  namespace  = "kube-system"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "kube-state-metrics"
}

/* Grafana Loki - logs storage */

resource "kubernetes_namespace" "log_storage" {
  metadata {
    name = "log-storage"
  }
}

resource "helm_release" "loki" {
  name       = "loki"
  namespace  = kubernetes_namespace.log_storage.metadata[0].name
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki-stack"
  version    = "2.5.1"

  dynamic "set" {
    for_each = {
      "promtail.enabled" = "true"
      "loki.persistence.enabled" = "true"
      "loki.persistence.size" = "10Gi"
      "loki.config.chunk_store_config.max_look_back_period" = "4200h"
      "loki.config.table_manager.retention_deletes_enabled" = "true"
      "loki.config.table_manager.retention_period" = "4200h"
    }
    content {
      name  = set.key
      value = set.value
    }
  }

}

resource "helm_release" "grafana" {
  name       = "grafana"
  namespace  = kubernetes_namespace.log_storage.metadata[0].name
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"

  dynamic "set" {
    for_each = {
      "image.tag" = var.grafana_version
      "persistence.enabled" = "true"
      "persistence.type" = "pvc"
      "persistence.size" = "10Gi"
      "adminUser" = var.grafana_user
      "adminPassword" = var.grafana_password
      "datasources.datasources\\.yaml.apiVersion" = "1"
      "datasources.datasources\\.yaml.datasources[0].name" = "Loki"
      "datasources.datasources\\.yaml.datasources[0].type" = "loki"
      "datasources.datasources\\.yaml.datasources[0].url" = "http://loki:3100"
      "datasources.datasources\\.yaml.datasources[0].access" = "proxy"
      "datasources.datasources\\.yaml.datasources[0].isDefault" = "true"
      "dashboardProviders.dashboardproviders\\.yaml.apiVersion" = "1"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].name" = "default"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].orgId" = "1"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].folder" = ""
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].folderUid" = ""
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].type" = "file"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].editable" = "true"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].disableDeletion" = "false"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].options.path" = "/var/lib/grafana/dashboards/default"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].options.foldersFromFilesStructure" = "true"
      "dashboards.default.log-storage.url" = "https://raw.githubusercontent.com/20tab/20tab-standard-project/main/grafana/dashboards/k8s-logs.json"

    }
    content {
      name  = set.key
      value = set.value
    }
  }

}

/* DNS Records */

resource "digitalocean_record" "main" {
  count = var.project_domain != "" ? 1 : 0

  domain = data.digitalocean_domain.main[0].name
  type   = "A"
  name   = local.domain_prefix
  value  = data.digitalocean_loadbalancer.main.ip
}

/* Grafana Ingress */

resource "kubernetes_ingress_v1" "grafana" {
  count = local.grafana_domain != "" || local.grafana_domain != "${local.domain_prefix}." ? 1 : 0

  metadata {
    name      = "log-storage-ingress"
    namespace = helm_release.grafana.namespace
    annotations = merge(
      {
        "kubernetes.io/ingress.class"                      = "traefik"
        "traefik.ingress.kubernetes.io/router.entrypoints" = "web,websecure"
      },
    )
  }

  spec {
    tls {
      hosts = ["${local.grafana_domain}"]
    }
    rule {
      host = "${local.grafana_domain}"
      http {
        path {
          backend {
            service {
              name = "grafana"
              port {
                number = 80
              }
            }
          }
          path = "/"
        }
      }
    }
  }
}
