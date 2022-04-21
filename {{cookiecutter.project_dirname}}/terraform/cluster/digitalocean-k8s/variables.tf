variable "create_domain" {
  description = "If true, create a DigitalOcean domain for project domain."
  type        = bool
  default     = true
}

variable "digitalocean_token" {
  description = "The DigitalOcean access token."
  type        = string
  sensitive   = true
}

variable "domain_prefixes" {
  description = "The list of domain prefixes."
  type        = list(string)
  default     = []
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

variable "letsencrypt_certificate_email" {
  description = "The email used to issue the Let's Encrypt certificate."
  type        = string
  default     = ""
}

variable "monitoring_domain_prefix" {
  description = "The monitoring domain url."
  type        = string
  default     = ""
}

variable "monitoring_url" {
  description = "The full monitoring url."
  type        = string
  default     = ""
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

variable "ssl_enabled" {
  description = "Tell if SSL should be enabled."
  type        = bool
  default     = false
}

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
}
