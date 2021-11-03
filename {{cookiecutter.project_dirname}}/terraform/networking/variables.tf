variable "digitalocean_token" {
  description = "The Digital Ocean access token."
  type        = string
  sensitive   = true
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
