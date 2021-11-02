variable "backend_service_port" {
  description = "The backend service port."
  type        = number
  default     = 8000
}

variable "backend_service_slug" {
  description = "The backend service slug."
  type        = string
  default     = "django"
}

variable "digitalocean_token" {
  description = "The Digital Ocean access token."
  type        = string
  sensitive   = true
}

variable "frontend_service_port" {
  description = "The frontend service port."
  type        = number
  default     = 3000
}

variable "frontend_service_slug" {
  description = "The frontend service slug."
  type        = string
  default     = "nextjs"
}

variable "k8s_cluster_region" {
  description = "The Digital Ocean Kubernetes cluster region."
  type        = string
  default     = ""
}

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

variable "project_slug" {
  description = "The project slug."
  type        = string
}

variable "stack_envs" {
  description = "A dict containing the stack environments settings."
  type        = map(map(any))
  default     = {}
}

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
  default     = "main"
}
