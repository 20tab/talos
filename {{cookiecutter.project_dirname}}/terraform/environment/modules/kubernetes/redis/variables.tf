variable "namespace" {
  description = "The namespace for Kubernetes resources."
  type        = string
}

variable "redis_image" {
  description = "The Redis Docker image."
  type        = string
  default     = "redis:6"
}

variable "resources_prefix" {
  description = "The prefix for Kubernetes resources names."
  type        = string
}
