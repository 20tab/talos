output "database_url" {
  description = "The Postgres database url."
  value       = "postgres://${var.database_user}:${random_password.main.result}@${kubernetes_service_v1.main.metadata[0].name}:5432/${var.database_name}"
  sensitive   = true
}
