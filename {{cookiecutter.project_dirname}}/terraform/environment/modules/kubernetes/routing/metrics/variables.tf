variable "basic_auth_password" {
  description = "The basic_auth password."
  type        = string
  sensitive   = true
  default     = ""
}

variable "basic_auth_ready" {
  description = "Tell if the basic auth is ready to be enabled."
  type        = bool
  default     = false
}

variable "basic_auth_username" {
  description = "The basic_auth username."
  type        = string
  default     = ""
}

variable "project_host" {
  description = "The project host."
  type        = string
}

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
}