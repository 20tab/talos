variable "digitalocean_token" {
  description = "The DigitalOcean access token."
  type        = string
  sensitive   = true
}

variable "grafana_password" {
  description = "The grafana admin password."
  type        = string
  sensitive   = true
}

variable "grafana_user" {
  description = "The grafana admin username."
  type        = string
  default     = "admin"
}

variable "grafana_version" {
  description = "The Grafana version."
  type        = string
  default     = "8.4.2"
}

variable "project_domain" {
  description = "The project domain."
  type        = string
  default     = ""
}

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
}

variable "use_monitoring" {
  description = "If 'true', enable the monitoring stack."
  type        = string
  default     = "true"
}
