variable "media_storage" {
  description = "The media storage solution."
  type        = string
}

variable "namespace" {
  description = "The namespace for Kubernetes resources."
  type        = string
}

variable "s3_access_id" {
  description = "The S3 bucket access key ID."
  type        = string
  sensitive   = true
}

variable "s3_backup_path" {
  description = "The S3 backup path."
  type        = string
  default     = "backup/postgres"
}

variable "s3_bucket_name" {
  description = "The S3 bucket name."
  type        = string
}

variable "s3_host" {
  description = "The S3 bucket host."
  type        = string
}

variable "s3_region" {
  description = "The S3 bucket region."
  type        = string
}

variable "s3_secret_key" {
  description = "The S3 bucket secret access key."
  type        = string
  sensitive   = true
}
