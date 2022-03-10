variable "backend_service_port" {
  description = "The backend service port."
  type        = number
  default     = {{ cookiecutter.backend_service_port }}
}

variable "database_connection_pool_size" {
  description = "The Digital Ocean database connection pool size."
  type        = number
  default     = 1
}

variable "digitalocean_token" {
  description = "The Digital Ocean access token."
  type        = string
  sensitive   = true
}

variable "frontend_service_port" {
  description = "The frontend service port."
  type        = number
  default     = {{ cookiecutter.frontend_service_port }}
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

# variable "gitlab_token" {
#   description = "The Gitlab token."
#   type        = string
#   sensitive   = true
# }

variable "media_storage" {
  description = "The media storage solution."
  type        = string
  default     = "{{ cookiecutter.media_storage }}"
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

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
}
