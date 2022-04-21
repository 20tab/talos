terraform {
  backend "local" {
  }

  required_providers {
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "~> 3.13"
    }
    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.30"
    }
  }
}

provider "gitlab" {
  token = var.gitlab_token
}

provider "tfe" {
  hostname = var.terraform_cloud_hostname
  token    = var.terraform_cloud_token
}

/* GitLab */

module "gitlab" {
  source = "./modules/gitlab"

  gitlab_token = var.gitlab_token

  local_repository_dir = var.service_dir

  group_name        = var.project_name
  group_slug        = var.gitlab_group_slug
  group_variables   = var.gitlab_group_variables
  group_owners      = var.gitlab_group_owners
  group_maintainers = var.gitlab_group_maintainers
  group_developers  = var.gitlab_group_developers

  project_name        = title(var.service_slug)
  project_description = "The \"${var.project_name}\" project ${var.service_slug} service."
  project_slug        = var.service_slug
  project_variables   = var.gitlab_project_variables
}

resource "gitlab_group_variable" "registry_password" {
  count = var.terraform_cloud_token == "" ? 1 : 0

  group     = module.gitlab.gitlab_group_id
  key       = "REGISTRY_PASSWORD"
  value     = module.gitlab.registry_deploy_token_value
  protected = true
  masked    = true
}

resource "gitlab_group_variable" "registry_username" {
  count = var.terraform_cloud_token == "" ? 1 : 0

  group     = module.gitlab.gitlab_group_id
  key       = "REGISTRY_USERNAME"
  value     = module.gitlab.registry_deploy_token_username
  protected = true
  masked    = true
}


/* Terraform Cloud */

module "terraform_cloud" {
  count = var.terraform_cloud_token != "" ? 1 : 0

  source = "./modules/terraform-cloud"
}
