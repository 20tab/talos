variable "grafana_password" {
  description = "The Grafana admin password."
  type        = string
  sensitive   = true
}

variable "grafana_user" {
  description = "The Grafana admin username."
  type        = string
}

variable "grafana_version" {
  description = "The Grafana version."
  type        = string
}

variable "grafana_persistence_enabled" {
  description = "Enable grafana persistence."
  type        = bool
  default     = false
}
