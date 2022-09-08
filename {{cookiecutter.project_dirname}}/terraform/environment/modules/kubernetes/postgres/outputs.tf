output "database_url" {
  description = "The postgres database url."
  value       = kubernetes_secret_v1.database_url.data.DATABASE_URL
}
