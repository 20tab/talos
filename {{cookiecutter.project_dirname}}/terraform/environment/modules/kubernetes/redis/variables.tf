variable "namespace" {
  description = "The namespace for Kubernetes resources."
  type        = string
}

variable "redis_image" {
  description = "The Redis Docker image."
  type        = string
  default     = "redis:6"
}
