terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
  }
}

resource "kubernetes_secret_v1" "main" {
  metadata {
    name      = "postgres-dump"
    namespace = var.namespace
  }

  data = {
    AWS_ACCESS_KEY_ID     = var.s3_access_id
    AWS_SECRET_ACCESS_KEY = var.s3_secret_key
    DATABASE_URL          = var.database_url
  }
}

resource "kubernetes_config_map_v1" "main" {
  metadata {
    name      = "postgres-dump"
    namespace = var.namespace
  }

  data = {
    AWS_S3_BACKUP_PATH      = var.s3_backup_path
    AWS_S3_HOST             = var.s3_host
    AWS_S3_REGION           = var.s3_region
    AWS_STORAGE_BUCKET_NAME = var.s3_bucket_name
  }
}

resource "kubernetes_cron_job_v1" "main" {
  metadata {
    name      = "postgresql-dump-cron"
    namespace = var.namespace
  }

  spec {
    schedule                      = "0 0 * * *"
    successful_jobs_history_limit = 31
    job_template {
      metadata {}
      spec {
        template {
          metadata {}
          spec {
            container {
              name    = "postgresql-dump-to-s3"
              image   = "20tab/postgres-dump-restore-to-from-s3:latest"
              command = ["/pg_dump_to_s3.sh"]
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
            restart_policy = "OnFailure"
          }
        }
      }
    }
  }
}
