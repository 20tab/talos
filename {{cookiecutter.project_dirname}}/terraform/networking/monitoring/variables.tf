variable "domain_prefix" {
  description = "The monitoring stack domain prefix."
  type        = string
  default     = "logs"
}

variable "grafana_password" {
  description = "The grafana admin password."
  type        = string
  sensitive   = true
}

variable "grafana_user" {
  description = "The grafana admin username."
  type        = string
}

variable "grafana_version" {
  description = "The Grafana version."
  type        = string
}

variable "project_domain" {
  description = "The project domain."
  type        = string
  default     = ""
}
