output "cache_url" {
  description = "The Redis cache url."
  value       = "redis://:${random_password.main.result}@${kubernetes_service_v1.main.metadata[0].name}:6379"
  sensitive   = true
}
