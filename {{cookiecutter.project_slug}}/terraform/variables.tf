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

variable "do_20tab_ssh_key_names" {
  description = "A digitalocean ssh public key name list."
  type        = list
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
