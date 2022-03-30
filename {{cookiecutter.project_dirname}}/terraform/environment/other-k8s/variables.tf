variable "backend_middlewares" {
  description = "The backend middlewares list."
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

variable "domain_prefix" {
  description = "The environment domain prefix (e.g. 'www')."
  type        = string
  default     = ""
}

variable "env_slug" {
  description = "The environment slug (e.g. 'prod')."
  type        = string
}

variable "frontend_middlewares" {
  description = "The frontend middlewares list."
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

variable "media_storage" {
  description = "The media storage solution."
  type        = string
  default     = "local"
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
  default     = ""
}

variable "postgres_persistent_volume_host_path" {
  description = "The persistent volume host path."
  type        = string
}

variable "project_domain" {
  description = "The project domain."
  type        = string
  default     = ""
}

variable "project_url" {
  description = "The project url."
  type        = string
  default     = ""
}

variable "redis_image" {
  description = "The Redis Docker image."
  type        = string
  default     = "redis:6"
}

variable "registry_password" {
  description = "The image registry password."
  type        = string
  sensitive   = true
}

variable "registry_username" {
  description = "The image registry username."
  type        = string
  default     = ""
}

variable "registry_server" {
  description = "The image registry server."
  type        = string
  default     = "registry.gitlab.com"
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

variable "use_redis" {
  description = "If 'true', a Redis database is created."
  type        = string
  default     = "false"
}
