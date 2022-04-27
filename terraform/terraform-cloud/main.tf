locals {
  organization = var.create_organization ? tfe_organization.main[0] : data.tfe_organization.main[0]

  workspaces = concat(
    flatten(
      [
        for stage in ["base", "cluster"] :
        [
          for stack in var.stacks :
          {
            name        = "${var.project_slug}_${var.service_slug}_${stage}_${stack}"
            description = "${var.project_name} project, ${var.service_slug} service, ${stack} stack, ${stage} stage"
            tags = [
              "project:${var.project_slug}",
              "service:${var.service_slug}",
              "stage:${stage}",
              "stack:${stack}",
            ]
          }
        ]
      ]
    ),
    [
      for env in var.environments :
      {
        name        = "${var.project_slug}_${var.service_slug}_environment_${env}"
        description = "${var.project_name} project, ${var.service_slug} service, ${env} environment"
        tags = [
          "project:${var.project_slug}",
          "service:${var.service_slug}",
          "stage:environment",
          "env:${env}",
        ]
      }
    ]
  )
}

terraform {
  backend "local" {
  }

  required_providers {
    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.30"
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

/* Workspaces */

resource "tfe_workspace" "test" {
  for_each = { for i in local.workspaces : i.name => i }

  name           = each.value.name
  description    = each.value.description
  organization   = local.organization.name
  execution_mode = "local"
  tag_names      = each.value.tags
}
