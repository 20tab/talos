terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
}

/* Metrics Server */

resource "helm_release" "metrics_server" {
  name             = "metrics-server"
  repository       = "https://kubernetes-sigs.github.io/metrics-server"
  chart            = "metrics-server"
  version          = "3.12.0"

  namespace        = "metrics-server"

  create_namespace = true

  values = [file("${path.module}/metrics-server/values.yaml")]
}

/* Kube State Metrics */

resource "helm_release" "kube_state_metrics" {
  name       = "kube-state-metrics"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "kube-state-metrics"
  version    = "3.16.2"

  namespace  = "kube-system"
}
