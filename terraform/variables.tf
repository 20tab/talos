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

variable "gitlab_group_slug" {
  description = "The slug of the Gitlab group."
  type        = string
}

variable "gitlab_group_variables" {
  description = "A map of Gitlab group variables to create."
  type        = map(map(any))
  default     = {}
}

variable "gitlab_project_variables" {
  description = "A map of Gitlab project variables to create."
  type        = map(map(any))
  default     = {}
}

variable "gitlab_token" {
  description = "The Gitlab token."
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "The project name."
  type        = string
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}

variable "service_dir" {
  description = "The service directory."
  type        = string
}

variable "service_slug" {
  description = "The service slug."
  type        = string
}
