variable "backend_service_extra_middlewares" {
  description = "The backend service additional middlewares."
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
  description = "Tell if the basic auth should be enabled."
  type        = bool
  default     = false
}

variable "basic_auth_password" {
  description = "The basic_auth password."
  type        = string
  sensitive   = true
  default     = ""
}

variable "basic_auth_ready" {
  description = "Tell if the basic auth is ready to be enabled."
  type        = bool
  default     = false
}

variable "basic_auth_username" {
  description = "The basic_auth username."
  type        = string
  default     = ""
}

variable "frontend_service_extra_middlewares" {
  description = "The frontend service additional middlewares."
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

variable "letsencrypt_certificate_email" {
  description = "The email used to issue the Let's Encrypt certificate."
  type        = string
  default     = ""
}

variable "letsencrypt_server" {
  description = "The Let's Encrypt server used to generate certificates."
  type        = string
  default     = ""
}

variable "monitoring_subdomain" {
  description = "The monitoring subdomain, if enabled."
  type        = string
  default     = ""
}

variable "namespace" {
  description = "The namespace for Kubernetes resources."
  type        = string
}

variable "project_domain" {
  description = "The project domain."
  type        = string
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
