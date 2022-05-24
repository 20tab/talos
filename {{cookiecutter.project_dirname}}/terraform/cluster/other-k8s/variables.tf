variable "kubernetes_cluster_ca_certificate" {
  description = "The base64 encoded Kubernetes CA certificate."
  type        = string
  sensitive   = true
}

variable "kubernetes_host" {
  description = "The Kubernetes host."
  type        = string
}

variable "kubernetes_token" {
  description = "A Kubernetes admin token."
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
