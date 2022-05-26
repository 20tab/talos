variable "digitalocean_token" {
  description = "The DigitalOcean access token."
  type        = string
  sensitive   = true
}

variable "letsencrypt_certificate_email" {
  description = "The email used to issue the Let's Encrypt certificate."
  type        = string
  default     = ""
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
}
