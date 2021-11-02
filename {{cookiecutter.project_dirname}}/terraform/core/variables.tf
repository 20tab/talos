variable "database_cluster_engine" {
  description = "The Digital Ocean database cluster engine."
  type        = string
  default     = "pg"
}

variable "database_cluster_node_count" {
  description = "The Digital Ocean database cluster nodes count."
  type        = number
  default     = 1
}

variable "database_cluster_node_size" {
  description = "The Digital Ocean database cluster droplet size."
  type        = string
}

variable "database_cluster_region" {
  description = "The Digital Ocean database cluster region."
  type        = string
  default     = ""
}

variable "database_cluster_version" {
  description = "The Digital Ocean database cluster major version."
  type        = string
  default     = "13"
}

variable "digitalocean_token" {
  description = "The Digital Ocean access token."
  type        = string
  sensitive   = true
}

variable "k8s_cluster_region" {
  description = "The Digital Ocean Kubernetes cluster region."
  type        = string
  default     = ""
}

variable "k8s_cluster_node_count" {
  description = "The Digital Ocean Kubernetes nodes count."
  type        = number
  default     = 1
}

variable "k8s_cluster_node_min_memory" {
  description = "The Digital Ocean Kubernetes nodes candidate minimum memory (in GB)."
  type        = number
  default     = 2
}

variable "k8s_cluster_node_min_vcpus" {
  description = "The Digital Ocean Kubernetes nodes candidate minimum number of vCPUs."
  type        = number
  default     = 1
}

variable "k8s_cluster_node_max_memory" {
  description = "The Digital Ocean Kubernetes nodes candidate maximum memory (in GB)."
  type        = number
  default     = 16
}

variable "k8s_cluster_node_max_vcpus" {
  description = "The Digital Ocean Kubernetes nodes candidate maximum number of vCPUs."
  type        = number
  default     = 4
}

variable "k8s_cluster_node_size" {
  description = "The Digital Ocean Kubernetes node size."
  type        = string
  default     = ""
}

variable "k8s_cluster_version" {
  description = "The Digital Ocean Kubernetes cluster version."
  type        = string
  default     = ""
}

variable "project_domain" {
  description = "The project domain."
  type        = string
  default     = ""
}

variable "project_slug" {
  description = "The project slug."
  type        = string
}

variable "s3_bucket_access_id" {
  description = "The S3 bucket access key ID."
  type        = string
  sensitive   = true
}

variable "s3_bucket_region" {
  description = "The Digital Ocean S3 Spaces region."
  type        = string
  default     = ""
}

variable "s3_bucket_secret_key" {
  description = "The S3 bucket secret access key."
  type        = string
  sensitive   = true
}

variable "stack_slug" {
  description = "The stack slug (e.g. 'main')."
  type        = string
  default     = "main"
}
