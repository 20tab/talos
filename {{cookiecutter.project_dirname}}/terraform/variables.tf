variable "do_token" {
  description = "The Digitalocean token."
  type        = string
  sensitive   = true
}

variable "gitlab_token" {
  description = "The Gitlab token."
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "The project name."
  type        = string
  sensitive   = true
}

variable "project_slug" {
  description = "The project slug."
  type        = string
  sensitive   = true
}

variable "project_domain" {
  description = "The project domain."
  type        = string
  sensitive   = true
}
