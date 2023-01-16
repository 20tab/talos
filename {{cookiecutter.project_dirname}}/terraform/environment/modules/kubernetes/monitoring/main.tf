locals {
  namespace = kubernetes_namespace_v1.log_storage.metadata[0].name
}

terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.6"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.13"
    }
  }
}

/* Kube State Metrics */

resource "helm_release" "kube_state_metrics" {
  name       = "kube-state-metrics"
  namespace  = "kube-system"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "kube-state-metrics"
}

/* Grafana Loki - logs storage */

resource "kubernetes_namespace_v1" "log_storage" {
  metadata {
    name = "log-storage"
  }
}

resource "helm_release" "loki" {
  name       = "loki"
  namespace  = local.namespace
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki-stack"
  version    = "2.6.1"

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

/* Grafana */

resource "kubernetes_config_map_v1" "k8s_logs_dashboard" {

  metadata {
    name      = "grafana-k8s-logs-dashboard"
    namespace = local.namespace
  }

  data = {
    "k8s-logs.json" = file("${path.module}/grafana/dashboards/k8s-logs.json")
  }
}

resource "helm_release" "grafana" {
  name       = "grafana"
  namespace  = local.namespace
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"

  values = [file("${path.module}/grafana/values.yaml")]

  dynamic "set" {
    for_each = {
      "image.tag"           = var.grafana_version
      "adminUser"           = var.grafana_user
      "adminPassword"       = var.grafana_password
      "persistence.enabled" = var.grafana_persistence_enabled
    }
    content {
      name  = set.key
      value = set.value
    }
  }

  depends_on = [kubernetes_config_map_v1.k8s_logs_dashboard]
}
