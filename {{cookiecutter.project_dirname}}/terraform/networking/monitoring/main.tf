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
    }
    content {
      name  = set.key
      value = set.value
    }
  }

}

/* Grafana Ingress */

resource "kubernetes_ingress" "grafana" {
  count = var.project_domain != "" ? 1 : 0

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
      hosts = ["${var.domain_prefix}.${var.project_domain}"]
    }
    rule {
      host = "${var.domain_prefix}.${var.project_domain}"
      http {
        path {
          backend {
            service_name = "grafana"
            service_port = 80
          }
          path = "/"
        }
      }
    }
  }
}
