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

variable "database_connection_pool_size" {
  description = "The DigitalOcean database connection pool size."
  type        = number
  default     = 1
}

variable "digitalocean_token" {
  description = "The DigitalOcean access token."
  type        = string
  sensitive   = true
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

variable "project_url" {
  description = "The project url."
  type        = string
  default     = ""
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
  description = "If 'true', a DigitalOcean Redis database is created."
  type        = string
  default     = "false"
}
