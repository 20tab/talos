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

variable "basic_auth_username" {
  description = "The basic_auth username."
  type        = string
  default     = ""
}

variable "env_slug" {
  description = "The environment slug (e.g. 'prod')."
  type        = string
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

variable "secondary_domains" {
  description = "An optional list of secondary domains to redirect to the main one."
  type        = list(string)
  default     = []
}

variable "subdomains" {
  description = "The subdomains associated to the environment."
  type        = list(string)
  default     = []

  validation {
    condition     = length(var.subdomains) > 0
    error_message = "At least one subdomain must be specified."
  }
}

variable "tls_certificate_crt" {
  description = "The base64-encoded PEM-formatted TLS full certificate."
  type        = string
  sensitive   = true
  default     = ""
}

variable "tls_certificate_key" {
  description = "The base64-encoded PEM-formatted TLS private key."
  type        = string
  sensitive   = true
  default     = ""
}
