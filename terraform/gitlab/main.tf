locals {
  create_group = length(regexall("^https\\://(?:www\\.)?gitlab\\.com/?", var.gitlab_url)) == 0 || var.group_namespace_path != ""
  group_id     = local.create_group ? gitlab_group.main[0].id : data.gitlab_group.main[0].id

  user_data = jsondecode(data.http.user_info.response_body)

  git_config_args = "-c user.email=${local.user_data.email} -c user.name=\"${local.user_data.name}\""

  escaped_base_ssh_url = replace(replace(gitlab_project.main.ssh_url_to_repo, "/${var.project_slug}.git", ""), "/", "\\/")

  reserved_member_ids = toset([tostring(local.user_data.id)])
  owners = setsubtract(
    toset([for i in data.gitlab_users.owners : tostring(i.users[0].id) if length(i.users) > 0]),
    local.reserved_member_ids,
  )
  maintainers = setsubtract(
    toset([for i in data.gitlab_users.maintainers : tostring(i.users[0].id) if length(i.users) > 0]),
    setunion(local.reserved_member_ids, local.owners),
  )
  developers = setsubtract(
    toset([for i in data.gitlab_users.developers : tostring(i.users[0].id) if length(i.users) > 0]),
    setunion(local.reserved_member_ids, local.owners, local.maintainers),
  )
}

terraform {
  backend "local" {
  }

  required_providers {
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "~> 16.10.0"
    }
  }
}

provider "gitlab" {
  token = var.gitlab_token
}

/* User Info */

data "http" "user_info" {
  url = "${var.gitlab_url}/api/v4/user"

  request_headers = {
    Accept        = "application/json"
    Authorization = "Bearer ${var.gitlab_token}"
  }
}

/* Group */

data "gitlab_group" "main" {
  count = local.create_group ? 0 : 1

  full_path = var.group_slug

  # Restore resourse once fixed https://gitlab.com/gitlab-org/gitlab/-/issues/244345
}

data "gitlab_group" "parent" {
  count = var.group_namespace_path != "" && local.create_group ? 1 : 0

  full_path = var.group_namespace_path
}

resource "gitlab_group" "main" {
  count = local.create_group ? 1 : 0

  name             = var.group_name
  path             = var.group_slug
  parent_id        = var.group_namespace_path == "" ? 0 : data.gitlab_group.parent[0].id
  visibility_level = "private"
}

/* Project */

resource "gitlab_project" "main" {
  name                   = var.project_name
  path                   = var.project_slug
  description            = var.project_description
  namespace_id           = local.group_id
  initialize_with_readme = false
  shared_runners_enabled = true
}

resource "null_resource" "init_repo" {
  depends_on = [gitlab_branch_protection.main]

  triggers = { project_id = gitlab_project.main.id }

  provisioner "local-exec" {
    command = join(" && ", [
      "cd ${var.local_repository_dir}",
      format(
        join(" && ", [
          "sed -i 's/__VCS_BASE_SSH_URL__/${local.escaped_base_ssh_url}/' README.md",
          "git init --initial-branch=main",
          "git remote add origin %s",
          "git add .",
          "git ${local.git_config_args} commit -m 'Initial commit'",
          "git push -u origin main -o ci.skip",
          "git remote set-url origin %s",
        ]),
        replace(
          gitlab_project.main.http_url_to_repo,
          "/^https://(.*)$/",
          "https://oauth2:${var.gitlab_token}@$1"
        ),
        gitlab_project.main.ssh_url_to_repo,
      )
    ])
  }
}

/* Branch Protections */

resource "gitlab_branch_protection" "main" {
  project            = gitlab_project.main.id
  branch             = "main"
  push_access_level  = "maintainer"
  merge_access_level = "developer"
}

/* Group Memberships */

data "gitlab_users" "owners" {
  for_each = toset(compact(split(",", var.group_owners)))

  search = trimspace(each.key)
}

resource "gitlab_group_membership" "owners" {
  for_each = local.owners

  group_id     = local.group_id
  user_id      = each.value
  access_level = "owner"
}

data "gitlab_users" "maintainers" {
  for_each = toset(compact(split(",", var.group_maintainers)))

  search = trimspace(each.key)
}

resource "gitlab_group_membership" "maintainers" {
  for_each = local.maintainers

  group_id     = local.group_id
  user_id      = each.value
  access_level = "maintainer"
}

data "gitlab_users" "developers" {
  for_each = toset(compact(split(",", var.group_developers)))

  search = trimspace(each.key)
}

resource "gitlab_group_membership" "developers" {
  for_each = local.developers

  group_id     = local.group_id
  user_id      = each.value
  access_level = "developer"
}

/* Deploy Token */

resource "gitlab_deploy_token" "regcred" {
  group    = local.group_id
  name     = "Kubernetes registry credentials"
  username = "${var.group_slug}-k8s-regcred"
  scopes   = ["read_registry"]
}

/* Badges */

resource "gitlab_group_badge" "pipeline" {
  group     = local.group_id
  link_url  = "https://gitlab.com/%%{project_path}/pipelines"
  image_url = "https://gitlab.com/%%{project_path}/badges/%%{default_branch}/pipeline.svg"
}

/* Group Variables */

resource "gitlab_group_variable" "vars" {
  for_each = var.group_variables

  group     = local.group_id
  key       = each.key
  value     = each.value.value
  protected = lookup(each.value, "protected", true)
  masked    = lookup(each.value, "masked", false)
}

resource "gitlab_group_variable" "registry_password" {
  count = var.use_vault ? 0 : 1

  group     = local.group_id
  key       = "REGISTRY_PASSWORD"
  value     = gitlab_deploy_token.regcred.token
  protected = true
  masked    = true
}

resource "gitlab_group_variable" "registry_username" {
  count = var.use_vault ? 0 : 1

  group     = local.group_id
  key       = "REGISTRY_USERNAME"
  value     = gitlab_deploy_token.regcred.username
  protected = true
  masked    = true
}

/* Project Variables */

resource "gitlab_project_variable" "vars" {
  for_each = var.project_variables

  project           = gitlab_project.main.id
  key               = each.key
  value             = each.value.value
  protected         = lookup(each.value, "protected", true)
  masked            = lookup(each.value, "masked", false)
  environment_scope = lookup(each.value, "environment_scope", "*")
}
