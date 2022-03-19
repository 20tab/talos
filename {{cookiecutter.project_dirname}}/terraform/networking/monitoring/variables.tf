variable "grafana_domain" {
  description = "The Grafana domain url."
  type        = string
  default     = ""
}

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

variable "project_domain" {
  description = "The project domain."
  type        = string
  default     = ""
}

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
}
