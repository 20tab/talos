variable "backend_service_extra_traefik_middlewares" {
  description = "The backend service additional Traefik middlewares."
  type        = list(string)
  default     = []
}

variable "backend_service_paths" {
  description = "The backend service paths."
  type        = list(string)
  default     = []
}

variable "backend_service_port" {
  description = "The backend service port."
  type        = number
  default     = 8000
}

variable "backend_service_slug" {
  description = "The backend service slug."
  type        = string
  default     = ""
}

variable "basic_auth_enabled" {
  description = "The basic_auth switch."
  type        = string
  default     = ""
}

variable "basic_auth_password" {
  description = "The basic_auth password."
  type        = string
  sensitive   = true
  default     = ""
}

variable "basic_auth_username" {
  description = "The basic_auth username."
  type        = string
  default     = ""
}

variable "database_dumps_enabled" {
  description = "Enable database dumps."
  type        = bool
  default     = false
}

variable "env_slug" {
  description = "The environment slug (e.g. 'prod')."
  type        = string
}

variable "frontend_service_extra_traefik_middlewares" {
  description = "The frontend service additional Traefik middlewares."
  type        = list(string)
  default     = []
}

variable "frontend_service_paths" {
  description = "The frontend service paths."
  type        = list(string)
  default     = []
}

variable "frontend_service_port" {
  description = "The frontend service port."
  type        = number
  default     = 3000
}

variable "frontend_service_slug" {
  description = "The frontend service slug."
  type        = string
  default     = ""
}

variable "grafana_password" {
  description = "The Grafana admin password."
  type        = string
  sensitive   = true
  default     = ""
}

variable "grafana_user" {
  description = "The Grafana admin username."
  type        = string
  default     = "admin"
}

variable "grafana_version" {
  description = "The Grafana version."
  type        = string
  default     = "8.4.2"
}

variable "kubernetes_cluster_ca_certificate" {
  description = "The base64 encoded Kubernetes CA certificate."
  type        = string
  sensitive   = true
}

variable "kubernetes_host" {
  description = "The Kubernetes host."
  type        = string
}

variable "kubernetes_token" {
  description = "A Kubernetes admin token."
  type        = string
  sensitive   = true
}

variable "letsencrypt_certificate_email" {
  description = "The email used to issue the Let's Encrypt certificate."
  type        = string
  default     = ""
}

variable "monitoring_subdomain" {
  description = "The monitoring subdomain."
  type        = string
  default     = ""
}

variable "postgres_image" {
  description = "The Postgres Docker image."
  type        = string
  default     = "postgres:14"
}

variable "postgres_persistent_volume_capacity" {
  description = "The persistent volume capacity (e.g. 1Gi)."
  type        = string
  default     = "10Gi"
}

variable "postgres_persistent_volume_claim_capacity" {
  description = "The persistent volume claim capacity (e.g. 1Gi)."
  type        = string
  default     = "10Gi"
}

variable "postgres_persistent_volume_host_path" {
  description = "The persistent volume host path."
  type        = string
}

variable "project_domain" {
  description = "The project domain."
  type        = string
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}

variable "redis_image" {
  description = "The Redis Docker image."
  type        = string
  default     = "redis:6"
}

variable "registry_password" {
  description = "The Docker image registry password."
  type        = string
  sensitive   = true
}

variable "registry_server" {
  description = "The Docker image registry server."
  type        = string
}

variable "registry_username" {
  description = "The Docker image registry username."
  type        = string
  sensitive   = true
}

variable "s3_access_id" {
  description = "The S3 bucket access key ID."
  type        = string
  default     = ""
  sensitive   = true
}

variable "s3_bucket_name" {
  description = "The S3 bucket name."
  type        = string
  default     = ""
}

variable "s3_host" {
  description = "The S3 bucket host."
  type        = string
  default     = ""
}

variable "s3_region" {
  description = "The S3 bucket region."
  type        = string
  default     = ""
}

variable "s3_secret_key" {
  description = "The S3 bucket secret access key."
  type        = string
  default     = ""
  sensitive   = true
}

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
}

variable "subdomains" {
  description = "The subdomains associated to the environment."
  type        = list(string)
  default     = []
}

variable "tls_certificate_crt" {
  description = "The TLS certificate .crt file content."
  type        = string
  sensitive   = true
  default     = ""
}

variable "tls_certificate_key" {
  description = "The TLS certificate .key file content."
  type        = string
  sensitive   = true
  default     = ""
}

variable "use_redis" {
  description = "Tell if a Redis service is used."
  type        = bool
  default     = false
}
