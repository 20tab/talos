terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

/* Configurationn */

resource "random_password" "main" {
  length  = 50
  special = false
}

resource "kubernetes_config_map_v1" "main" {
  metadata {
    name      = "redis"
    namespace = var.namespace
  }

  data = {
    "redis.conf" = "requirepass \"${random_password.main.result}\"\n"
  }
}


/* Deployment */

resource "kubernetes_deployment_v1" "main" {
  metadata {
    name      = "redis"
    namespace = var.namespace
    annotations = {
      "reloader.stakater.com/auto" = "true"
    }
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        component = "redis"
      }
    }
    template {
      metadata {
        labels = {
          component = "redis"
        }
      }
      spec {
        volume {
          name = "redis"
          config_map {
            name = kubernetes_config_map_v1.main.metadata[0].name
          }
        }
        container {
          name    = "redis"
          image   = var.redis_image
          command = ["redis-server", "/etc/redis/redis.conf"]
          port {
            container_port = 6379
          }
          volume_mount {
            name       = "redis"
            mount_path = "/etc/redis"
          }
        }
      }
    }
  }
}

/* Cluster IP Service */

resource "kubernetes_service_v1" "main" {

  metadata {
    name      = "redis"
    namespace = var.namespace
  }
  spec {
    type = "ClusterIP"
    selector = {
      component = "redis"
    }
    port {
      port        = 6379
      target_port = 6379
    }

  }
}
