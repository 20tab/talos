locals {
  namespace = kubernetes_namespace_v1.log_storage.metadata[0].name

  s3_storage_enabled = alltrue(
    [
      var.s3_access_id != "",
      var.s3_bucket_name != "",
      var.s3_host != "",
      var.s3_region != "",
      var.s3_secret_key != "",
    ]
  )

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
  version    = "2.6.4"

  values = local.s3_storage_enabled ? [file("${path.module}/loki/values.yaml")] : []

  dynamic "set" {
    for_each = local.s3_storage_enabled ? {
      "loki.config.storage_config.aws.access_key_id"      = var.s3_access_id
      "loki.config.storage_config.aws.bucketnames"        = var.s3_bucket_name
      "loki.config.storage_config.aws.endpoint"           = var.s3_host
      "loki.config.storage_config.aws.region"             = var.s3_region
      "loki.config.storage_config.aws.secret_access_key"  = var.s3_secret_key
    } : {
      "loki.config.chunk_store_config.max_look_back_period" = "4400h"
      "loki.config.limits_config.max_query_length"          = "2200h"
      "loki.config.table_manager.retention_deletes_enabled" = "true"
      "loki.config.table_manager.retention_period"          = "4400h"
      "loki.persistence.enabled"                            = "true"
      "loki.persistence.size"                               = "10Gi"
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
      "image.tag"     = var.grafana_version
      "adminUser"     = var.grafana_user
      "adminPassword" = var.grafana_password
    }
    content {
      name  = set.key
      value = set.value
    }
  }

  depends_on = [kubernetes_config_map_v1.k8s_logs_dashboard]
}
