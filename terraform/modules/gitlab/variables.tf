
variable "gitlab_token" {
  description = "The GitLab token."
  type        = string
  sensitive   = true
}

variable "group_developers" {
  description = "The comma-separeted GitLab group developers usernames."
  type        = string
  default     = ""
}

variable "group_maintainers" {
  description = "The comma-separeted GitLab group maiantainers usernames."
  type        = string
  default     = ""
}

variable "group_name" {
  description = "The GitLab group name."
  type        = string
}

variable "group_owners" {
  description = "The comma-separeted GitLab group owners usernames."
  type        = string
}

variable "group_slug" {
  description = "The GitLab group slug."
  type        = string
}

variable "group_variables" {
  description = "A map of GitLab group variables to create."
  type        = map(map(any))
  default     = {}
}

variable "local_repository_dir" {
  description = "The absolute path of the local repository directory."
  type        = string
}

variable "project_description" {
  description = "The GitLab project description."
  type        = string
}

variable "project_name" {
  description = "The GitLab project name."
  type        = string
}

variable "project_slug" {
  description = "The GitLab project slug."
  type        = string
}

variable "project_variables" {
  description = "A map of GitLab project variables to create."
  type        = map(map(any))
  default     = {}
}
