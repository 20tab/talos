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
