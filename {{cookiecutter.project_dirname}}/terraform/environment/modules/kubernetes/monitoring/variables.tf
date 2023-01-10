variable "grafana_password" {
  description = "The Grafana admin password."
  type        = string
  sensitive   = true
}

variable "grafana_user" {
  description = "The Grafana admin username."
  type        = string
}

variable "grafana_version" {
  description = "The Grafana version."
  type        = string
}

variable "s3_access_id" {
  description = "The S3 bucket access key ID."
  type        = string
  default     = ""
  sensitive   = true
}

variable "s3_bucket_name" {
  description = "The S3 bucket name."
  type        = string
  default     = ""
}

variable "s3_host" {
  description = "The S3 host url."
  type        = string
  default     = ""
}

variable "s3_region" {
  description = "The S3 bucket region."
  type        = string
  default     = ""
}

variable "s3_secret_key" {
  description = "The S3 bucket secret access key."
  type        = string
  default     = ""
  sensitive   = true
}
