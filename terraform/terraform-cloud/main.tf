locals {
  organization = var.create_organization ? tfe_organization.main[0] : data.tfe_organization.main[0]

  platform_core_workspaces = flatten([
    for cluster in var.clusters : [
      for provider in lookup(var.cluster_core_providers, cluster, []) : {
        name        = "${var.project_slug}_platform_${cluster}_core_${provider}"
        description = "${var.project_name} platform, ${cluster} cluster, ${provider} core."
        tags = [
          "project:${var.project_slug}",
          "layer:platform",
          "cluster:${cluster}",
          "component:core",
          "provider:${provider}",
        ]
      }
    ]
  ])

  platform_kubernetes_workspaces = [
    for cluster in var.clusters : {
      name        = "${var.project_slug}_platform_${cluster}_kubernetes"
      description = "${var.project_name} platform, ${cluster} cluster, kubernetes layer."
      tags = [
        "project:${var.project_slug}",
        "layer:platform",
        "cluster:${cluster}",
        "component:kubernetes",
      ]
    }
  ]

  workspaces = concat(
    local.platform_core_workspaces,
    local.platform_kubernetes_workspaces,
  )
}

terraform {
  backend "local" {
  }

  required_providers {
    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.70"
    }
  }
}

provider "tfe" {
  hostname = var.hostname
  token    = var.terraform_cloud_token
}

/* Organization */

data "tfe_organization" "main" {
  count = var.create_organization ? 0 : 1

  name = var.organization_name
}

resource "tfe_organization" "main" {
  count = var.create_organization ? 1 : 0

  name  = var.organization_name
  email = var.admin_email
}

/* Project (groups all workspaces; default execution mode is set on tfe_project_settings) */

resource "tfe_project" "main" {
  organization = local.organization.name
  name         = var.project_slug
  description  = "${var.project_name} project workspaces."
}

resource "tfe_project_settings" "main" {
  project_id             = tfe_project.main.id
  default_execution_mode = "local"
}

/* Workspaces */

resource "tfe_workspace" "main" {
  for_each = { for i in local.workspaces : i.name => i }

  name         = each.value.name
  description  = each.value.description
  organization = local.organization.name
  project_id   = tfe_project.main.id
  tag_names    = each.value.tags
}
