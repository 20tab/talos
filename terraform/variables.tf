variable "backend_type" {
  description = "The frontend service type."
  type        = string
  default     = "django"
}

variable "frontend_type" {
  description = "The frontend service type."
  type        = string
  default     = "react"
}

variable "gitlab_group_developers" {
  description = "The comma-separeted Gitlab group developers usernames."
  type        = string
  default     = ""
}

variable "gitlab_group_maintainers" {
  description = "The comma-separeted Gitlab group maiantainers usernames."
  type        = string
  default     = ""
}

variable "gitlab_group_owners" {
  description = "The comma-separeted Gitlab group owners usernames."
  type        = string
}

variable "gitlab_token" {
  description = "The Gitlab token."
  type        = string
  sensitive   = true
}

variable "project_description" {
  description = "The project description."
  type        = string
  default     = ""
}

variable "project_domain" {
  description = "The project domain."
  type        = string
}

variable "project_name" {
  description = "The project name."
  type        = string
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}
