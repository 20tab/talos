variable "project_name" {
  description = "The project name."
  type        = string
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}

variable "secrets" {
  description = "The secrets."
  type        = map(map(string))
  default     = {}
}

variable "terraform_cloud_role_max_ttl" {
  description = "The Terraform Cloud auth backend role max TTL."
  type        = number
  default     = 900
}

variable "terraform_cloud_role_ttl" {
  description = "The Terraform Cloud auth backend role TTL."
  type        = number
  default     = 900
}

variable "terraform_cloud_token" {
  description = "The Terraform Cloud User token."
  type        = string
  sensitive   = true
  default     = ""
}

variable "vault_address" {
  description = "The Vault address."
  type        = string
}

variable "vault_token" {
  description = "The Vault token."
  type        = string
  sensitive   = true
  default     = ""
}
