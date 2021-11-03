locals {
  project_slug = "{{ cookiecutter.project_slug }}"

  media_storage = "{{ cookiecutter.media_storage }}"

  digitalocean_default_region = "fra1"
  digitalocean_regions        = data.digitalocean_regions.main.regions[*].slug

  database_cluster_region = contains(
    local.digitalocean_regions,
    var.database_cluster_region
  ) ? var.database_cluster_region : local.digitalocean_default_region

  k8s_cluster_region = contains(
    local.digitalocean_regions,
    var.k8s_cluster_region
  ) ? var.k8s_cluster_region : local.digitalocean_default_region

  resource_name = var.stack_slug == "main" ? local.project_slug : "${local.project_slug}-${var.stack_slug}"
}

terraform {
  backend "http" {
  }

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

/* Providers */

provider "digitalocean" {
  token = var.digitalocean_token

  spaces_access_id  = var.s3_bucket_access_id
  spaces_secret_key = var.s3_bucket_secret_key
}

/* Data Sources */

data "digitalocean_kubernetes_versions" "main" {}

data "digitalocean_sizes" "k8s" {
  filter {
    key    = "vcpus"
    values = range(var.k8s_cluster_node_min_vcpus, var.k8s_cluster_node_max_vcpus)
  }

  filter {
    key    = "memory"
    values = [for i in range(var.k8s_cluster_node_min_memory, var.k8s_cluster_node_max_memory) : i * 1024]
  }

  filter {
    key    = "regions"
    values = [local.k8s_cluster_region]
  }

  sort {
    key       = "price_monthly"
    direction = "asc"
  }
}

data "digitalocean_regions" "main" {
  filter {
    key    = "available"
    values = ["true"]
  }
}

/* Kubernetes Cluster */

resource "digitalocean_kubernetes_cluster" "main" {
  name   = "${local.resource_name}-k8s-cluster"
  region = local.k8s_cluster_region
  version = coalesce(
    var.k8s_cluster_version,
    data.digitalocean_kubernetes_versions.main.latest_version
  )
  auto_upgrade = true

  node_pool {
    name       = "${local.resource_name}-k8s-node"
    node_count = var.k8s_cluster_node_count
    size = contains(
      data.digitalocean_sizes.k8s.sizes[*].slug,
      var.k8s_cluster_node_size
    ) ? var.k8s_cluster_node_size : element(data.digitalocean_sizes.k8s.sizes, 0).slug
  }

  maintenance_policy {
    start_time = "02:00"
    day        = "sunday"
  }

  timeouts {
    create = "60m"
  }
}

/* Spaces Bucket */

resource "digitalocean_spaces_bucket" "main" {
  count = local.media_storage == "s3-digitalocean" ? 1 : 0

  name = "${local.resource_name}-s3-bucket"
  region = contains(
    local.digitalocean_regions,
    var.s3_bucket_region
  ) ? var.s3_bucket_region : local.digitalocean_default_region
}

/* Database Cluster */

resource "digitalocean_database_cluster" "main" {
  name       = "${local.resource_name}-database-cluster"
  region     = local.database_cluster_region
  engine     = var.database_cluster_engine
  version    = var.database_cluster_version
  size       = var.database_cluster_node_size
  node_count = var.database_cluster_node_count

  maintenance_window {
    day  = "sunday"
    hour = "02:00"
  }

  timeouts {
    create = "60m"
  }
}

/* Domain */

resource "digitalocean_domain" "default" {
  count = var.create_domain && var.stack_slug == "main" && var.project_domain != "" ? 1 : 0

  name = var.project_domain
}
