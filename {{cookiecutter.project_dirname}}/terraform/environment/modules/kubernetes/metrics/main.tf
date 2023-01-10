terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.6"
    }
  }
}

/* Metrics Server */

resource "helm_release" "metrics_server" {
  name              = "metrics-server"
  namespace         = "metrics-server"
  repository        = "https://kubernetes-sigs.github.io/metrics-server"
  chart             = "metrics-server"
  create_namespace  = true
  version           = "3.8.2"

  values = [file("${path.module}/metrics-server/values.yaml")]
}

/* Kube State Metrics */

resource "helm_release" "kube_state_metrics" {
  name       = "kube-state-metrics"
  namespace  = "kube-system"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "kube-state-metrics"
}
