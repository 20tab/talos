locals {
  auth_slug = "gitlab-jwt-${var.project_slug}"
}


terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "3.7.0"
    }
  }
}

provider "vault" {
}

/* GitLab JWT Auth */

resource "vault_jwt_auth_backend" "gitlab_jwt" {
  description  = "Demonstration of the Terraform JWT auth backend"
  path         = local.auth_slug
  jwks_url     = format("%s/-/jwks", trimsuffix(var.gitlab_url, "/"))
  bound_issuer = var.gitlab_url
}

resource "vault_policy" "gitlab_jwt_stacks" {
  for_each = var.stacks_environments

  name = "${local.auth_slug}-stacks-${each.key}"

  policy = <<EOF
# Read-only permission for GitLab CI jobs on project "${var.project_name}" ${each.key} stack secrets

path "${var.project_slug}/stacks/${each.key}/*" {
  capabilities = [ "read" ]
}

path "${var.project_slug}-tfc/creds/default" {
  capabilities = [ "read" ]
}
EOF
}

resource "vault_jwt_auth_backend_role" "gitlab_jwt_stacks" {
  for_each = vault_policy.gitlab_jwt_stacks

  backend = vault_jwt_auth_backend.gitlab_jwt.path

  role_name = trimprefix(each.value.name, "${local.auth_slug}-")
  role_type = "jwt"

  token_explicit_max_ttl = var.gitlab_jwt_auth_token_explicit_max_ttl
  token_policies         = [each.value.name]

  user_claim = "user_email"

  bound_claims = { namespace_path = var.project_namespace_path }
}

resource "vault_policy" "gitlab_jwt_envs" {
  for_each = transpose({ for k, v in var.stacks_environments : k => keys(v) })

  name = "${local.auth_slug}-envs-${each.key}"

  policy = <<EOF
# Read-only permission for GitLab CI jobs on project "${var.project_name}" ${each.key} stack secrets

path "${var.project_slug}/stacks/${each.value[0]}/*" {
  capabilities = [ "read" ]
}

path "${var.project_slug}/envs/${each.key}/*" {
  capabilities = [ "read" ]
}

path "${var.project_slug}-tfc/creds/default" {
  capabilities = [ "read" ]
}
EOF
}

resource "vault_jwt_auth_backend_role" "envs" {
  for_each = vault_policy.gitlab_jwt_envs

  backend = vault_jwt_auth_backend.gitlab_jwt.path

  role_name = trimprefix(each.value.name, "${local.auth_slug}-")
  role_type = "jwt"

  token_explicit_max_ttl = var.gitlab_jwt_auth_token_explicit_max_ttl
  token_policies         = [each.value.name]

  user_claim = "user_email"

  bound_claims = { namespace_path = var.project_namespace_path }
}

resource "vault_policy" "gitlab_jwt_pact" {
  count = var.use_pact ? 1 : 0

  name = "${local.auth_slug}-pact"

  policy = <<EOF
# Read-only permission for GitLab CI jobs on project "${var.project_name}" Pact secrets

path "${var.project_slug}/pact" {
  capabilities = [ "read" ]
}
EOF
}

resource "vault_jwt_auth_backend_role" "gitlab_jwt_pact" {
  count = var.use_pact ? 1 : 0

  backend = vault_jwt_auth_backend.gitlab_jwt.path

  role_name = "pact"
  role_type = "jwt"

  token_explicit_max_ttl = var.gitlab_jwt_auth_token_explicit_max_ttl
  token_policies         = [vault_policy.gitlab_jwt_pact[0].name]

  user_claim = "user_email"

  bound_claims = { namespace_path = var.project_namespace_path }
}

/* GitLab OIDC Auth */

data "vault_auth_backend" "gitlab_oidc" {
  count = var.gitlab_oidc_auth_path != "" ? 1 : 0

  path = var.gitlab_oidc_auth_path
}

resource "vault_policy" "gitlab_oidc" {
  count = var.gitlab_oidc_auth_path != "" ? 1 : 0

  name = "gitlab-oidc-${var.project_slug}"

  policy = <<EOF
# Full permission for GitLab group members on project "${var.project_name}" secrets

path "sys/mounts" {
  capabilities = [ "read" ]
}

# Manage KV secrets
path "sys/mounts/${var.project_slug}" {
  capabilities = [ "create", "delete", "update" ]
}

path "${var.project_slug}" {
  capabilities = [ "list" ]
}

path "${var.project_slug}/*" {
  capabilities = [ "create", "delete", "list", "read", "update" ]
}

# Manage TFC secrets
path "sys/mounts/${var.project_slug}-tfc" {
  capabilities = [ "create", "delete", "update" ]
}

path "${var.project_slug}-tfc" {
  capabilities = [ "list" ]
}

path "${var.project_slug}-tfc/*" {
  capabilities = [ "create", "delete", "list", "read", "update" ]
}

# Enable child token generation for the Terraform Vault provider
# https://registry.terraform.io/providers/hashicorp/vault/latest/docs#token
path "auth/token/create" {
  capabilities = [ "create", "update" ]
}
EOF
}

resource "vault_identity_group" "gitlab_oidc" {
  count = var.gitlab_oidc_auth_path != "" ? 1 : 0

  name     = var.project_slug
  type     = "external"
  policies = [vault_policy.gitlab_oidc[0].name]
}

resource "vault_identity_group_alias" "gitlab_oidc" {
  count = var.gitlab_oidc_auth_path != "" ? 1 : 0

  name           = var.project_namespace_path
  mount_accessor = data.vault_auth_backend.gitlab_oidc[0].accessor
  canonical_id   = vault_identity_group.gitlab_oidc[0].id
}
