variable "database_name" {
  description = "The Postgres database name."
  type        = string
}

variable "database_user" {
  description = "The Postgres database user."
  type        = string
}

variable "namespace" {
  description = "The namespace for Kubernetes resources."
  type        = string
}

variable "persistent_volume_capacity" {
  description = "The persistent volume capacity (e.g. 1Gi)."
  type        = string
  default     = "10Gi"
}

variable "persistent_volume_claim_capacity" {
  description = "The persistent volume claim capacity (e.g. 1Gi)."
  type        = string
  default     = ""
}

variable "persistent_volume_host_path" {
  description = "The persistent volume host path."
  type        = string
}

variable "postgres_image" {
  description = "The Postgres Docker image."
  type        = string
  default     = "postgres:14"
}

variable "resources_prefix" {
  description = "The prefix for Kubernetes resources names."
  type        = string
}
