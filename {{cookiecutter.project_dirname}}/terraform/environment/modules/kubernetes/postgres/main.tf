terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.9.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

/* Volumes */

resource "kubernetes_persistent_volume_v1" "main" {
  metadata {
    name      = "${var.resources_prefix}-postgres"
  }
  spec {
    capacity = {
      storage = var.persistent_volume_capacity
    }
    access_modes = ["ReadWriteOnce"]
    persistent_volume_source {
      host_path {
        path = var.persistent_volume_host_path
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim_v1" "main" {
  metadata {
    name      = "${var.resources_prefix}-postgres"
    namespace = var.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = coalesce(
          var.persistent_volume_claim_capacity,
          var.persistent_volume_capacity
        )
      }
    }
    volume_name = kubernetes_persistent_volume_v1.main.metadata[0].name
  }
}

/* Configuration  */

resource "random_password" "main" {
  length = 50
}

resource "kubernetes_secret_v1" "main" {
  metadata {
    name      = "${var.resources_prefix}-postgres"
    namespace = var.namespace
  }
  data = {
    POSTGRES_USER     = var.database_user
    POSTGRES_PASSWORD = random_password.main.result
  }
}

resource "kubernetes_config_map_v1" "main" {
  metadata {
    name      = "${var.resources_prefix}-postgres"
    namespace = var.namespace
  }
  data = {
    POSTGRES_DB = var.database_name
  }
}

/* Deployment */

resource "kubernetes_deployment_v1" "main" {
  metadata {
    name      = "${var.resources_prefix}-postgres"
    namespace = var.namespace
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        component = "${var.resources_prefix}-postgres"
      }
    }
    template {
      metadata {
        labels = {
          component = "${var.resources_prefix}-postgres"
        }
      }
      spec {
        volume {
          name = "${var.resources_prefix}-postgres"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.main.metadata[0].name
          }
        }
        container {
          name  = "postgres"
          image = var.postgres_image
          port {
            container_port = 5432
          }
          volume_mount {
            name       = "${var.resources_prefix}-postgres"
            mount_path = "/var/lib/postgresql/data"
            sub_path   = "postgres"
          }
          env_from {
            config_map_ref {
              name = kubernetes_config_map_v1.main.metadata[0].name
            }
          }
          env_from {
            secret_ref {
              name = kubernetes_secret_v1.main.metadata[0].name
            }
          }
        }
      }
    }
  }
}

/* Cluster IP Service */

resource "kubernetes_service_v1" "main" {
  metadata {
    name      = "${var.resources_prefix}-postgres"
    namespace = var.namespace
  }
  spec {
    type = "ClusterIP"
    selector = {
      component = "${var.resources_prefix}-postgres"
    }
    port {
      port        = 5432
      target_port = 5432
    }
  }
  depends_on = [kubernetes_deployment_v1.main]
}

/* Secrets */

resource "kubernetes_secret_v1" "database_url" {
  metadata {
    name      = "${var.resources_prefix}-database-url"
    namespace = var.namespace
  }
  data = {
    DATABASE_URL = "postgres://${var.database_user}:${random_password.main.result}@${var.resources_prefix}-postgres:5432/${var.database_name}"
  }
}
