output "redis_url" {
  description = "The Redis server URL."
  value       = "redis://:${random_password.main.result}@${kubernetes_service_v1.main.metadata[0].name}:6379"
  sensitive   = true
}
