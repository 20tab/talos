variable "auth_backend_path" {
  description = "The path of the auth backend to associate the project group to."
  type        = string
  default     = ""
}

variable "project_name" {
  description = "The project name."
  type        = string
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}
