locals {
  secrets_mount_path = coalesce(var.gitlab_group_slug, var.project_slug)

  gitlab_enabled = var.gitlab_url != "" && var.gitlab_group_slug != ""
  gitlab_url     = local.gitlab_enabled ? trimsuffix(var.gitlab_url, "/") : ""
}

terraform {
  backend "local" {
  }

  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "3.7.0"
    }
  }
}

provider "vault" {}

/* Terraform Cloud user */

data "http" "tfc_user_info" {
  count = var.terraform_cloud_token != "" ? 1 : 0

  url = "https://app.terraform.io/api/v2/account/details"

  request_headers = {
    Accept        = "application/json"
    Authorization = "Bearer ${var.terraform_cloud_token}"
  }
}

/* Secrets Engines */

resource "vault_mount" "main" {
  path = local.secrets_mount_path

  description = "The ${var.project_name} project secrets."

  type = "kv"
  options = {
    version = "1"
  }
}

resource "vault_terraform_cloud_secret_backend" "main" {
  count = var.terraform_cloud_token != "" ? 1 : 0

  backend = "${var.project_slug}-tfc"

  description = "The ${var.project_name} project Terraform Cloud secrets engine."

  token = var.terraform_cloud_token
}

resource "vault_terraform_cloud_secret_role" "main" {
  count = var.terraform_cloud_token != "" ? 1 : 0

  backend = vault_terraform_cloud_secret_backend.main[0].backend
  name    = "default"
  user_id = jsondecode(data.http.tfc_user_info[0].body).data.id

  max_ttl = var.terraform_cloud_role_max_ttl
  ttl     = var.terraform_cloud_role_ttl
}

/* Secrets */

resource "vault_generic_secret" "common" {
  for_each = var.common_secrets

  path = "${vault_mount.main.path}/common/${each.key}/secrets"

  data_json = jsonencode(each.value)
}

resource "vault_generic_secret" "service" {
  for_each = var.service_secrets

  path = "${vault_mount.main.path}/${var.service_slug}/${each.key}/secrets"

  data_json = jsonencode(each.value)
}

/* GitLab JWT Auth */

resource "vault_jwt_auth_backend" "gitlab" {
  count = local.gitlab_enabled ? 1 : 0

  description  = "GitLab JWT auth backend for the \"${var.project_name}\" project."
  path         = "gitlab-jwt-${var.project_slug}"
  jwks_url     = "${local.gitlab.url}/-/jwks"
  bound_issuer = local.gitlab_url
}

resource "vault_policy" "gitlab_read" {
  count = local.gitlab_enabled ? 1 : 0

  name = "gitlab-${var.project_slug}-read"

  policy = <<EOF
# Read-only permission for GitLab CI jobs on project "${var.project_name}" secrets

path "{{identity.entity.aliases.${vault_jwt_auth_backend.gitlab[0].accessor}.metadata.project_path}}/*" {
  capabilities = [ "read" ]
}

path "{{identity.entity.aliases.${vault_jwt_auth_backend.gitlab[0].accessor}.metadata.project_slug}}/ci-jobs" {
  capabilities = [ "read" ]
}

path "{{identity.entity.aliases.${vault_jwt_auth_backend.gitlab[0].accessor}.metadata.project_slug}}-tfc/creds/default" {
  capabilities = [ "read" ]
}
EOF
}

resource "vault_jwt_auth_backend_role" "main" {
  count = local.gitlab_enabled ? 1 : 0

  backend = vault_jwt_auth_backend.gitlab[0].path

  role_name = "default"
  role_type = "jwt"

  token_explicit_max_ttl = var.gitlab_jwt_auth_token_explicit_max_ttl
  token_policies         = [vault_policy.gitlab_read[0].name]

  user_claim = "user_email"

  bound_claims_type = "glob"
  bound_claims      = { namespace_path = var.gitlab_group_slug }
  claim_mappings = {
    namespace_path = "project_slug",
    project_path   = "project_path",
  }
}
