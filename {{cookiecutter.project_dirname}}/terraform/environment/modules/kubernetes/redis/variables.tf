variable "key_prefix" {
  description = "The key prefix."
  type        = string
  default     = ""
}

variable "namespace" {
  description = "The namespace for Kubernetes resources."
  type        = string
}

variable "redis_image" {
  description = "The Redis Docker image."
  type        = string
  default     = "redis:6"
}
