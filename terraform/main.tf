locals {
  user_data = jsondecode(data.http.user_info.body)

  git_config = "-c user.email=${local.user_data.email} -c user.name=\"${local.user_data.name}\""

  reserved_member_ids = toset([tostring(local.user_data.id)])
  owners = setsubtract(
    toset([for i in data.gitlab_users.owners : tostring(i.users[0].id) if length(i.users) > 0]),
    local.reserved_member_ids,
  )
  maintainers = setsubtract(
    setsubtract(
      toset([for i in data.gitlab_users.maintainers : tostring(i.users[0].id) if length(i.users) > 0]),
      local.owners
    ),
    local.reserved_member_ids,
  )
  developers = setsubtract(
    setsubtract(
      setsubtract(
        toset([for i in data.gitlab_users.developers : tostring(i.users[0].id) if length(i.users) > 0]),
        local.maintainers
      ),
      local.owners
    ),
    local.reserved_member_ids,
  )
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

/* Data Sources */

data "gitlab_group" "group" {
  full_path = var.gitlab_group_slug
  # Gitlab group resource atm cannot be create: https://gitlab.com/gitlab-org/gitlab/-/issues/244345
  # name             = var.project_name
  # path             = var.project_slug
  # description      = var.project_description
  # visibility_level = "private"
}

data "http" "user_info" {
  url = "https://gitlab.com/api/v4/user"

  request_headers = {
    Accept        = "application/json"
    Authorization = "Bearer ${var.gitlab_token}"
  }
}

/* Project */

resource "gitlab_project" "main" {
  name                   = title(var.service_slug)
  path                   = var.service_slug
  description            = "The \"${var.project_name}\" project ${var.service_slug} service."
  namespace_id           = data.gitlab_group.group.id
  initialize_with_readme = false
}

resource "null_resource" "init_repo" {
  depends_on = [gitlab_branch_protection.develop]

  triggers = {
    service_project_id = gitlab_project.main.id
  }

  provisioner "local-exec" {
    command = join(" && ", [
      "cd ${var.service_dir}",
      format(
        join(" && ", [
          "git init --initial-branch=develop",
          "git remote add origin %s",
          "git add .",
          "git ${local.git_config} commit -m 'Initial commit'",
          "git push -u origin develop -o ci.skip",
          "git checkout -b master",
          "git push -u origin master -o ci.skip",
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

resource "gitlab_branch_protection" "develop" {
  project            = gitlab_project.main.id
  branch             = "develop"
  push_access_level  = "maintainer"
  merge_access_level = "developer"
}

resource "gitlab_branch_protection" "master" {
  depends_on = [null_resource.init_repo]

  project            = gitlab_project.main.id
  branch             = "master"
  push_access_level  = "no one"
  merge_access_level = "maintainer"
}

resource "gitlab_tag_protection" "tags" {
  project             = gitlab_project.main.id
  tag                 = "*"
  create_access_level = "maintainer"
}

/* Group Memberships */

data "gitlab_users" "owners" {
  for_each = toset(compact(split(",", var.gitlab_group_owners)))

  search = trimspace(each.key)
}

resource "gitlab_group_membership" "owners" {
  for_each = local.owners

  group_id     = data.gitlab_group.group.id
  user_id      = each.value
  access_level = "owner"
}

data "gitlab_users" "maintainers" {
  for_each = toset(compact(split(",", var.gitlab_group_maintainers)))

  search = trimspace(each.key)
}

resource "gitlab_group_membership" "maintainers" {
  for_each = local.maintainers

  group_id     = data.gitlab_group.group.id
  user_id      = each.value
  access_level = "maintainer"
}

data "gitlab_users" "developers" {
  for_each = toset(compact(split(",", var.gitlab_group_developers)))

  search = trimspace(each.key)
}

resource "gitlab_group_membership" "developers" {
  for_each = local.developers

  group_id     = data.gitlab_group.group.id
  user_id      = each.value
  access_level = "developer"
}

/* Group Variables */

resource "gitlab_group_variable" "vars" {
  for_each = var.gitlab_group_variables

  group     = data.gitlab_group.group.id
  key       = each.key
  value     = each.value.value
  protected = lookup(each.value, "protected", true)
  masked    = lookup(each.value, "masked", true)
}

/* Project Variables */

resource "gitlab_project_variable" "vars" {
  for_each = var.gitlab_project_variables

  project           = gitlab_project.main.id
  key               = each.key
  value             = each.value.value
  protected         = lookup(each.value, "protected", true)
  masked            = lookup(each.value, "masked", true)
  environment_scope = lookup(each.value, "environment_scope", "*")
}