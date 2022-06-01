variable "common_secrets" {
  description = "The common secrets."
  type        = map(map(string))
  default     = {}
}

variable "project_name" {
  description = "The project name."
  type        = string
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}

variable "service_secrets" {
  description = "The service secrets."
  type        = map(map(string))
  default     = {}
}

variable "service_slug" {
  description = "The service slug."
  type        = string
}

variable "terraform_cloud_role_ttl" {
  description = "The Terraform Cloud auth backend role TTL."
  type        = number
  default     = 900
}

variable "terraform_cloud_role_max_ttl" {
  description = "The Terraform Cloud auth backend role max TTL."
  type        = number
  default     = 900
}

variable "terraform_cloud_token" {
  description = "The Terraform Cloud User token."
  type        = string
  sensitive   = true
  default     = ""
}
