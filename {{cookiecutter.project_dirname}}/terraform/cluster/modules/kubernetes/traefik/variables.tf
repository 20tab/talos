variable "letsencrypt_certificate_email" {
  description = "The email used to issue the Let's Encrypt certificate."
  type        = string
  default     = ""
}

variable "load_balancer_annotations" {
  description = "The Load Balancer service annotations."
  type        = map(string)
  default     = {}
}

variable "traefik_helm_chart_version" {
  description = "The helm chart Traefik version https://github.com/traefik/traefik-helm-chart/releases."
  type        = string
  default     = "26.0.0"
}
