variable "admin_email" {
  description = "The Terraform Cloud Organization admin email."
  type        = string
  default     = ""
}

variable "create_organization" {
  description = "Tell if the Terraform Cloud organization should be created."
  type        = bool
  default     = false
}

variable "hostname" {
  description = "The Terraform Cloud hostname."
  type        = string
  default     = "app.terraform.io"
}

variable "organization_name" {
  description = "The Terraform Cloud Organization name."
  type        = string
}

variable "project_name" {
  description = "The project name."
  type        = string
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}

variable "clusters" {
  description = "The list of cluster slugs (e.g. [\"dev\", \"main\"])."
  type        = list(string)
  default     = []
}

variable "cluster_core_providers" {
  description = "Per-cluster core providers map (e.g. {dev = [\"aws\", \"digitalocean\"]})."
  type        = map(list(string))
  default     = {}
}

variable "terraform_cloud_token" {
  description = "The Terraform Cloud token."
  type        = string
  sensitive   = true
  default     = ""
}
