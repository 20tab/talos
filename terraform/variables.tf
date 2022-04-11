variable "gitlab_group_developers" {
  description = "The comma-separeted GitLab group developers usernames."
  type        = string
  default     = ""
}

variable "gitlab_group_maintainers" {
  description = "The comma-separeted GitLab group maiantainers usernames."
  type        = string
  default     = ""
}

variable "gitlab_group_owners" {
  description = "The comma-separeted GitLab group owners usernames."
  type        = string
}

variable "gitlab_group_slug" {
  description = "The slug of the GitLab group."
  type        = string
}

variable "gitlab_group_variables" {
  description = "A map of GitLab group variables to create."
  type        = map(map(any))
  default     = {}
}

variable "gitlab_project_variables" {
  description = "A map of GitLab project variables to create."
  type        = map(map(any))
  default     = {}
}

variable "gitlab_token" {
  description = "The GitLab token."
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

variable "terraform_cloud_hostname" {
  description = "The Terraform Cloud hostname."
  type        = string
  default     = "app.terraform.io"
}

variable "terraform_cloud_token" {
  description = "The Terraform Cloud token."
  type        = string
  sensitive   = true
  default     = ""
}
