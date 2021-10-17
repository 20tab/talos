locals {
  backend_count    = var.backend_type == "django" ? 1 : 0
  backend_project  = gitlab_project.backend[0]
  frontend_count   = var.frontend_type == "react" ? 1 : 0
  frontend_project = gitlab_project.frontend[0]

  init_command = join(" && ", [
    "git init",
    "git add .",
    "git commit -m 'Initialize the repository'",
    "git remote add origin %s",
    "git push -u origin master -o ci.skip",
    "git checkout -b develop",
    "git push -u origin develop -o ci.skip"
  ])
}

terraform {
  backend "local" {
  }

  required_providers {
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "3.7.0"
    }
  }
}

provider "gitlab" {
  token = var.gitlab_token
}

data "gitlab_group" "group" {
  full_path = var.project_slug
  # Gitlab group resource atm cannot be create: https://gitlab.com/gitlab-org/gitlab/-/issues/244345
  # name             = var.project_name
  # path             = var.project_slug
  # description      = var.project_description
  # visibility_level = "private"
}

resource "gitlab_project" "orchestrator" {
  name         = "Orchestrator"
  description  = "The \"${var.project_name}\" project orchestrator service."
  namespace_id = data.gitlab_group.group.id
  default_branch = "develop"
}

resource "null_resource" "init_orchestrator" {
  triggers = {
    orchestrator_project_id = gitlab_project.orchestrator.id
  }

  provisioner "local-exec" {
    command = join(" && ", [
      "cd ../${var.project_slug}",
      "sed -i -e \"s/__GITLAB_GROUP__/${var.project_slug}/\" README.md",
      format(local.init_command, gitlab_project.orchestrator.ssh_url_to_repo)
    ])
  }
}

resource "gitlab_branch_protection" "develop_orchestrator" {
  project            = gitlab_project.orchestrator.id
  branch             = "develop"
  push_access_level  = "maintainer"
  merge_access_level = "developer"
}

resource "gitlab_branch_protection" "master_orchestrator" {
  project            = gitlab_project.orchestrator.id
  branch             = "master"
  push_access_level  = "no one"
  merge_access_level = "maintainer"
}

resource "gitlab_tag_protection" "tags_orchestrator" {
  project             = gitlab_project.orchestrator.id
  tag                 = "*"
  create_access_level = "maintainer"
}

resource "gitlab_project" "backend" {
  count = local.backend_count

  name         = "Backend"
  description  = "The \"${var.project_name}\" project backend service."
  namespace_id = data.gitlab_group.group.id
  default_branch = "develop"
}

resource "null_resource" "init_backend" {
  count = local.backend_count

  triggers = {
    backend_project_id = local.backend_project.id
  }

  provisioner "local-exec" {
    command = join(" && ", [
      "cd ../${var.project_slug}/backend",
      format(local.init_command, local.backend_project.ssh_url_to_repo)
    ])
  }
}

resource "gitlab_branch_protection" "develop_backend" {
  count = local.backend_count

  project            = local.backend_project.id
  branch             = "develop"
  push_access_level  = "maintainer"
  merge_access_level = "developer"
}

resource "gitlab_branch_protection" "master_backend" {
  count = local.backend_count

  project            = local.backend_project.id
  branch             = "master"
  push_access_level  = "no one"
  merge_access_level = "maintainer"
}

resource "gitlab_tag_protection" "tags_backend" {
  count = local.backend_count

  project             = local.backend_project.id
  tag                 = "*"
  create_access_level = "maintainer"
}

resource "gitlab_project_badge" "coverage_backend" {
  count = local.backend_count

  project   = local.backend_project.id
  link_url  = "https://${var.project_slug}.gitlab.io/backend/htmlcov/"
  image_url = "https://gitlab.com/\\%\\{project_path}/badges/\\%\\{default_branch}/coverage.svg"
}

resource "gitlab_project_badge" "pipeline_backend" {
  count = local.backend_count

  project   = local.backend_project.id
  link_url  = "https://gitlab.com/\\%\\{project_path}/pipelines"
  image_url = "https://gitlab.com/\\%\\{project_path}/badges/\\%\\{default_branch}/pipeline.svg"
}

resource "gitlab_project" "frontend" {
  count = local.frontend_count

  name         = "Frontend"
  description  = "The \"${var.project_name}\" project frontend service."
  namespace_id = data.gitlab_group.group.id
  default_branch = "develop"
}

resource "null_resource" "init_frontend" {
  count = local.frontend_count

  triggers = {
    frontend_project_id = local.frontend_project.id
  }

  provisioner "local-exec" {
    command = join(" && ", [
      "cd ../${var.project_slug}/frontend",
      format(local.init_command, local.frontend_project.ssh_url_to_repo)
    ])
  }
}

resource "gitlab_branch_protection" "develop_frontend" {
  count = local.frontend_count

  project            = local.frontend_project.id
  branch             = "develop"
  push_access_level  = "maintainer"
  merge_access_level = "developer"
}

resource "gitlab_branch_protection" "master_frontend" {
  count = local.frontend_count

  project            = local.frontend_project.id
  branch             = "master"
  push_access_level  = "no one"
  merge_access_level = "maintainer"
}

resource "gitlab_tag_protection" "tags_frontend" {
  count = local.frontend_count

  project             = local.frontend_project.id
  tag                 = "*"
  create_access_level = "maintainer"
}

resource "gitlab_project_badge" "coverage_frontend" {
  count = local.frontend_count

  project   = local.frontend_project.id
  link_url  = "https://${var.project_slug}.gitlab.io/frontend/"
  image_url = "https://gitlab.com/\\%\\{project_path}/badges/\\%\\{default_branch}/pipeline.svg"
}

resource "gitlab_project_badge" "pipeline_frontend" {
  count = local.frontend_count

  project   = local.frontend_project.id
  link_url  = "https://gitlab.com/\\%\\{project_path}/pipelines"
  image_url = "https://gitlab.com/\\%\\{project_path}/badges/\\%\\{default_branch}/pipeline.svg"
}

data "gitlab_user" "owners" {
  for_each = toset(compact(split(",", var.gitlab_group_owners)))

  username = each.key
}

resource "gitlab_group_membership" "owners" {
  for_each = {
    for k, v in data.gitlab_user.owners : k => v.id
  }

  group_id     = data.gitlab_group.group.id
  user_id      = each.value
  access_level = "owner"
}

data "gitlab_user" "maintainers" {
  for_each = toset(compact(split(",", var.gitlab_group_maintainers)))

  username = each.key
}

resource "gitlab_group_membership" "maintainers" {
  for_each = {
    for k, v in data.gitlab_user.maintainers : k => v.id
  }

  group_id     = data.gitlab_group.group.id
  user_id      = each.value
  access_level = "maintainer"
}

data "gitlab_user" "developers" {
  for_each = toset(compact(split(",", var.gitlab_group_developers)))

  username = each.key
}

resource "gitlab_group_membership" "developers" {
  for_each = {
    for k, v in data.gitlab_user.developers : k => v.id
  }

  group_id     = data.gitlab_group.group.id
  user_id      = each.value
  access_level = "developer"
}



# TODO
# - Fix escape in pipeline and move pipeline badge to group
# - Check default branch on checkout -b
