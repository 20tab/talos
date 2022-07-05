variable "gitlab_jwt_auth_token_explicit_max_ttl" {
  description = "The GitLab auth token explicit max TTL."
  type        = number
  default     = 60
}

variable "gitlab_oidc_auth_path" {
  description = "The GitLab OIDC auth Vault path."
  type        = string
  default     = ""
}

variable "gitlab_url" {
  description = "The GitLab url."
  type        = string
  default     = "https://gitlab.com"
}

variable "project_name" {
  description = "The project name."
  type        = string
}

variable "project_path" {
  description = "The project path."
  type        = string
}

variable "stacks_environments" {
  description = "The list of stacks slugs."
  type        = map(map(map(string)))
}
