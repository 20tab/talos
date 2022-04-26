variable "create_s3_bucket" {
  description = "Tell if a DigitalOcean Spaces bucket should be created."
  type        = bool
}

variable "database_cluster_engine" {
  description = "The DigitalOcean database cluster engine."
  type        = string
  default     = "pg"
}

variable "database_cluster_node_count" {
  description = "The DigitalOcean database cluster nodes count."
  type        = number
  default     = 1
}

variable "database_cluster_node_size" {
  description = "The DigitalOcean database cluster droplet size."
  type        = string
}

variable "database_cluster_region" {
  description = "The DigitalOcean database cluster region."
  type        = string
  default     = ""
}

variable "database_cluster_version" {
  description = "The DigitalOcean database cluster major version."
  type        = string
  default     = "14"
}

variable "digitalocean_token" {
  description = "The DigitalOcean access token."
  type        = string
  sensitive   = true
}

variable "k8s_cluster_region" {
  description = "The DigitalOcean Kubernetes cluster region."
  type        = string
  default     = ""
}

variable "k8s_cluster_node_count" {
  description = "The DigitalOcean Kubernetes nodes count."
  type        = number
  default     = 1
}

variable "k8s_cluster_node_min_memory" {
  description = "The DigitalOcean Kubernetes nodes candidate minimum memory (in GB)."
  type        = number
  default     = 2
}

variable "k8s_cluster_node_min_vcpus" {
  description = "The DigitalOcean Kubernetes nodes candidate minimum number of vCPUs."
  type        = number
  default     = 1
}

variable "k8s_cluster_node_max_memory" {
  description = "The DigitalOcean Kubernetes nodes candidate maximum memory (in GB)."
  type        = number
  default     = 16
}

variable "k8s_cluster_node_max_vcpus" {
  description = "The DigitalOcean Kubernetes nodes candidate maximum number of vCPUs."
  type        = number
  default     = 4
}

variable "k8s_cluster_node_size" {
  description = "The DigitalOcean Kubernetes node size."
  type        = string
  default     = ""
}

variable "k8s_cluster_version" {
  description = "The DigitalOcean Kubernetes cluster version."
  type        = string
  default     = ""
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}

variable "redis_cluster_node_count" {
  description = "The DigitalOcean Redis cluster nodes count."
  type        = number
  default     = 1
}

variable "redis_cluster_node_size" {
  description = "The DigitalOcean Redis cluster droplet size."
  type        = string
}

variable "redis_cluster_region" {
  description = "The DigitalOcean Redis cluster region."
  type        = string
  default     = ""
}
variable "redis_cluster_version" {
  description = "The DigitalOcean Redis cluster major version."
  type        = string
  default     = "6"
}

variable "s3_access_id" {
  description = "The S3 bucket access key ID."
  type        = string
  sensitive   = true
}

variable "s3_region" {
  description = "The S3 bucket region."
  type        = string
  default     = ""
}

variable "s3_secret_key" {
  description = "The S3 bucket secret access key."
  type        = string
  sensitive   = true
}

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
}

variable "ssl_enabled" {
  description = "Tell if SSL should be enabled."
  type        = bool
  default     = false
}

variable "use_redis" {
  description = "Tell if a Redis service is used."
  type        = bool
  default     = false
}
