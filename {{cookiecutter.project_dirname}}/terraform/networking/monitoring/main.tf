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
      "promtail.enabled"                                    = "true"
      "loki.persistence.enabled"                            = "true"
      "loki.persistence.size"                               = "10Gi"
      "loki.config.chunk_store_config.max_look_back_period" = "4200h"
      "loki.config.table_manager.retention_deletes_enabled" = "true"
      "loki.config.table_manager.retention_period"          = "4200h"
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
      "image.tag"                                                                                   = var.grafana_version
      "persistence.enabled"                                                                         = "true"
      "persistence.type"                                                                            = "pvc"
      "persistence.size"                                                                            = "10Gi"
      "adminUser"                                                                                   = var.grafana_user
      "adminPassword"                                                                               = var.grafana_password
      "datasources.datasources\\.yaml.apiVersion"                                                   = "1"
      "datasources.datasources\\.yaml.datasources[0].name"                                          = "Loki"
      "datasources.datasources\\.yaml.datasources[0].type"                                          = "loki"
      "datasources.datasources\\.yaml.datasources[0].url"                                           = "http://loki:3100"
      "datasources.datasources\\.yaml.datasources[0].access"                                        = "proxy"
      "datasources.datasources\\.yaml.datasources[0].isDefault"                                     = "true"
      "dashboardProviders.dashboardproviders\\.yaml.apiVersion"                                     = "1"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].name"                              = "default"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].orgId"                             = "1"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].folder"                            = ""
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].folderUid"                         = ""
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].type"                              = "file"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].editable"                          = "true"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].disableDeletion"                   = "false"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].options.path"                      = "/var/lib/grafana/dashboards/default"
      "dashboardProviders.dashboardproviders\\.yaml.providers[0].options.foldersFromFilesStructure" = "true"
      "dashboards.default.log-storage.url"                                                          = "./grafana-dashboards.json"
    }
    content {
      name  = set.key
      value = set.value
    }
  }

}

/* Grafana Ingress */

resource "kubernetes_ingress_v1" "grafana" {
  count = var.host == "" ? 0 : 1

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
      hosts = ["${var.host}"]
    }
    rule {
      host = var.host
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
